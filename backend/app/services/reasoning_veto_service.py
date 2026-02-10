"""
Post-answer reasoning analysis for diagnostic purposes.

"""

import logging
import re
from enum import Enum
from typing import TypedDict

logger = logging.getLogger(__name__)


# ============================================================
# VETO FRAMEWORK
# ============================================================


class VetoLevel(str, Enum):
    # Veto severity from reasoning.
    HARD = 'hard'  # Cannot proceed - must refuse
    SOFT = 'soft'  # Can proceed but must cap confidence + warn
    NONE = 'none'  # No veto - proceed normally


class ReasoningVeto(TypedDict):
    # Result of reasoning veto analysis.
    level: VetoLevel
    signals: list[str]  # Which red flags were detected
    confidence_cap: float  # Max allowed confidence (1.0 = no cap)
    reason: str  # Human-readable explanation
    should_refuse: bool  # If True, answer must be replaced with refusal
    refusal_message: str  # Pre-composed refusal if level == HARD


# ============================================================
# RED FLAGS: HARD VETOES (model explicitly says "I can't")
# ============================================================

REASONING_HARD_VETOES = [
    # Explicit impossibility
    r'\bcannot\s+confirm\b',
    r'\bcannot\s+verify\b',
    r'\bcannot\s+determine\b',
    r'\bimpossible\s+to\s+(?:say|determine|verify)\b',
    r'\bno\s+reliable\s+source',
    r'\bno\s+(?:sufficient\s+)?evidence',
    # Explicit data limitations
    r'\bno\s+(?:access|information)\s+(?:about|on|to)',
    r'\bnot\s+(?:covered|mentioned|addressed)\s+in\s+(?:the\s+)?(?:context|sources|files)',
    r'\boutside\s+(?:my|available)\s+(?:knowledge|context)',
    # Explicit contradiction
    r'\bconflicting\s+(?:sources|information)',
    r'\bsources?\s+(?:disagree|conflict)',
]


# ============================================================
# RED FLAGS: SOFT VETOES (model says "uncertain/speculative")
# ============================================================

REASONING_SOFT_VETOES = [
    # Uncertainty language
    r'\buncertain\b',
    r'\bspeculat(?:ion|ive)',
    r'\bprojection\b',
    r'\bmay\s+change\b',
    r'\best(?:imate|imation)\b',
    r'\bguess(?:ing|work)?\b',
    r'\bassum(?:ing|ption)',
    # Inference/inference-based
    r'\binfer(?:red|ence)?\b',
    r'\bdeduced?\b',
    r'\bconjectur',
    # Lack of confidence
    r'\bnot\s+certain\b',
    r'\bnot\s+confident\b',
    r'\bnot\s+sure\b',
    r'\blow\s+confidence\b',
    # Hedging
    r'\bseems?\s+(?:likely|probable)\b',
    r'\bprobably\b',
    r'\blikely\b',
]


# ============================================================
# ANALYZER
# ============================================================


def extract_reasoning_assertions(reasoning: str) -> dict:
    """
    Parse reasoning to extract what model asserts about its own confidence.

    """
    if not reasoning:
        return {
            'has_hard_veto': False,
            'hard_veto_signals': [],
            'has_soft_veto': False,
            'soft_veto_signals': [],
            'tone_analysis': {
                'confident_language': False,
                'uncertain_language': False,
                'contradictory': False,
            },
        }

    reasoning_lower = reasoning.lower()

    # Check hard vetoes
    hard_matches = []
    for pattern in REASONING_HARD_VETOES:
        if re.search(pattern, reasoning_lower, re.IGNORECASE):
            # Extract the matched phrase for clarity
            match = re.search(pattern, reasoning_lower, re.IGNORECASE)
            if match:
                hard_matches.append(match.group(0))

    # Check soft vetoes
    soft_matches = []
    for pattern in REASONING_SOFT_VETOES:
        if re.search(pattern, reasoning_lower, re.IGNORECASE):
            match = re.search(pattern, reasoning_lower, re.IGNORECASE)
            if match:
                soft_matches.append(match.group(0))

    # Tone analysis
    confident_patterns = [
        r'\b(?:clearly|definitely|certainly|without\s+doubt|proven)\b',
        r'\b(?:is\s+)?the\s+(?:answer|fact|case)\b',
    ]
    uncertain_patterns = [
        r'\b(?:might|could|may|possibly|arguably)\b',
        r'\b(?:seems?|appears?)\b',
        r'\bunsure\b',
    ]

    has_confident = any(re.search(p, reasoning_lower) for p in confident_patterns)
    has_uncertain = any(re.search(p, reasoning_lower) for p in uncertain_patterns)
    is_contradictory = has_confident and has_uncertain

    return {
        'has_hard_veto': bool(hard_matches),
        'hard_veto_signals': hard_matches,
        'has_soft_veto': bool(soft_matches),
        'soft_veto_signals': soft_matches,
        'tone_analysis': {
            'confident_language': has_confident,
            'uncertain_language': has_uncertain,
            'contradictory': is_contradictory,
        },
    }


def assess_reasoning_veto(
    reasoning: str,
    base_confidence: float,
    answer: str,
) -> ReasoningVeto:
    """
    Determine veto level from reasoning assertions (DIAGNOSTIC ONLY).

    This function analyzes reasoning for diagnostic purposes only.
    It does NOT modify answers or confidence - only returns metadata.

    """
    assertions = extract_reasoning_assertions(reasoning)

    # HARD VETO: Model explicitly says "cannot confirm/verify"
    # This is diagnostic only - we don't actually refuse
    if assertions['has_hard_veto']:
        hard_signals = assertions['hard_veto_signals']
        return ReasoningVeto(
            level=VetoLevel.HARD,
            signals=hard_signals,
            confidence_cap=0.0,  # Historical: what would have been applied
            reason=f'Reasoning explicitly states: {hard_signals[0]}',
            should_refuse=False,  # Always False in diagnostic mode
            refusal_message='',
        )

    # SOFT VETO: Model expresses uncertainty/speculation
    # This is diagnostic only - we don't actually cap confidence
    if assertions['has_soft_veto']:
        soft_signals = assertions['soft_veto_signals']

        # Check if reasoning contradicts answer tone
        answer_lower = answer.lower() if answer else ''
        answer_has_confident_tone = any(
            re.search(pattern, answer_lower)
            for pattern in [r'\bdefinitely\b', r'\bclearly\b', r'\bcertainly\b']
        )

        contradiction_detected = assertions['tone_analysis']['contradictory'] or (
            assertions['has_soft_veto'] and answer_has_confident_tone
        )

        # Cap confidence based on soft veto strength (for logging only)
        confidence_cap = 0.5 if contradiction_detected else 0.6 if len(soft_signals) >= 3 else 0.7

        reason = f'Reasoning expresses uncertainty: {", ".join(soft_signals[:2])}'

        if contradiction_detected:
            reason += ' (model contradicts itself with confident tone in answer)'

        return ReasoningVeto(
            level=VetoLevel.SOFT,
            signals=soft_signals,
            confidence_cap=min(base_confidence, confidence_cap),  # Historical value
            reason=reason,
            should_refuse=False,  # Always False in diagnostic mode
            refusal_message='',
        )

    # Reasoning supports answer
    return ReasoningVeto(
        level=VetoLevel.NONE,
        signals=[],
        confidence_cap=1.0,
        reason='Reasoning supports conclusion',
        should_refuse=False,
        refusal_message='',
    )
