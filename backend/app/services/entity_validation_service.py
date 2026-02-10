"""
Entity Validation Service

Handles entity extraction and validation against context sources.
Uses spaCy NLP when available, falls back to pattern-based extraction.

"""

import logging
import re

# NLP for entity extraction (optional - graceful fallback)
try:
    import spacy

    nlp = spacy.load('en_core_web_sm')
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    SPACY_AVAILABLE = False
    nlp = None

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Log NLP availability
if SPACY_AVAILABLE:
    logger.info('spaCy NLP loaded successfully for intelligent entity extraction')
else:
    logger.warning(
        'spaCy not available. Using pattern-based entity extraction. '
        'Install with: pip install spacy && python -m spacy download en_core_web_sm'
    )


def is_common_word(word: str) -> bool:
    """
    Check if word is a common/generic term that shouldn't be flagged.
    Uses pattern matching instead of exhaustive lists.

    """
    word_lower = word.lower()

    # Pattern 1: Single capital letter (A, I, etc.)
    if len(word) == 1:
        return True

    # Pattern 2: Ends with common suffixes (likely adjectives/nationalities)
    common_suffixes = ('ian', 'ish', 'ese', 'ean', 'an', 'ern')
    if any(word_lower.endswith(suffix) for suffix in common_suffixes):
        return True  # American, British, Japanese, European, etc.

    # Pattern 3: Days of week (pattern: ends with 'day')
    if word_lower.endswith('day'):
        return True

    # Pattern 4: Months (pattern: length 3-9, ends with common month patterns)
    if len(word) >= 3 and any(
        word_lower.endswith(pattern)
        for pattern in ('uary', 'rch', 'il', 'ay', 'une', 'uly', 'ust', 'ber')
    ):
        return True

    # Pattern 5: Common tech/web terms (pattern: lowercase in context is common)
    tech_patterns = ('net', 'web', 'mail', 'site', 'line', 'book', 'tube', 'hub')
    if any(pattern in word_lower for pattern in tech_patterns):
        return True

    # Pattern 6: Programming languages (pattern: ends with common PL patterns)
    if any(word_lower.endswith(pattern) for pattern in ('script', 'thon', 'lang')):
        return True

    # Pattern 7: Common sentence starters (very short + high frequency)
    if word in {'The', 'This', 'That', 'These', 'Those', 'A', 'An', 'I'}:
        return True

    return False


def extract_entities_pattern_based(text: str) -> list[str]:
    """
    Pattern-based entity extraction (fallback when spaCy unavailable).

    """
    if not text:
        return []

    # Extract all capitalized phrases
    raw_entities = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text)

    filtered = []
    seen = set()

    for entity in raw_entities:
        # Skip common words
        if is_common_word(entity):
            continue

        # Skip very short single words (likely not entities)
        if len(entity) < 3 and ' ' not in entity:
            continue

        # De-duplicate
        entity_lower = entity.lower()
        if entity_lower in seen:
            continue

        seen.add(entity_lower)
        filtered.append(entity)

    return filtered


def extract_entities_nlp(text: str) -> list[str]:
    """
    NLP-powered entity extraction using spaCy.
    More accurate, reduces false positives.

    """
    if not text or not nlp:
        return []

    try:
        doc = nlp(text)

        # Only flag specific entity types that could be hallucinations:
        relevant_labels = {
            'PERSON',
            'ORG',
            'GPE',
            'PRODUCT',
            'EVENT',
            'WORK_OF_ART',
            'LAW',
            'NORP',
            'FAC',
        }

        entities = []
        seen = set()

        for ent in doc.ents:
            if ent.label_ not in relevant_labels:
                continue

            entity_text = ent.text.strip()

            # Skip common words even if tagged as entities
            if is_common_word(entity_text):
                continue

            # Deduplicate
            entity_lower = entity_text.lower()
            if entity_lower in seen:
                continue

            seen.add(entity_lower)
            entities.append(entity_text)

        logger.debug('NLP entity extraction: %s entities from %s chars', len(entities), len(text))

        return entities

    except Exception as e:
        logger.warning('spaCy entity extraction failed: %s. Using pattern fallback.', e)
        return extract_entities_pattern_based(text)


def extract_entities(text: str) -> list[str]:
    """
    Extract named entities with intelligent filtering.
    Uses spaCy NLP if available, falls back to pattern-based extraction.

    """
    if not text:
        return []

    # Use NLP if available, otherwise fall back to pattern matching
    if SPACY_AVAILABLE and nlp:
        entities = extract_entities_nlp(text)
        logger.debug('Entity extraction: NLP mode (spaCy) - %s entities', len(entities))
    else:
        entities = extract_entities_pattern_based(text)
        logger.debug('Entity extraction: Pattern mode (fallback) - %s entities', len(entities))

    return entities


def is_entity_in_context(entity: str, context: str) -> bool:
    """
    Check if entity appears in context using fuzzy matching.
    Handles: case-insensitive, partial matches, plurals.
    """
    entity_lower = entity.lower()
    context_lower = context.lower()

    # Strategy 1: Exact match
    if entity_lower in context_lower:
        return True

    # Strategy 2: Multi-word entity - check if ANY significant word appears
    parts = entity_lower.split()
    if len(parts) > 1:
        significant_parts = [p for p in parts if len(p) > 3]
        if any(part in context_lower for part in significant_parts):
            return True

    # Strategy 3: Stem matching (handles plurals/tenses)
    # "company" vs "companies", "running" vs "run"
    if len(entity_lower) > 5:
        stem = entity_lower[:5]
        if stem in context_lower:
            return True

    # Strategy 4: Check if entity is acronym expansion in context
    # "FBI" in context, "Federal Bureau Investigation" in answer
    if len(entity) > 10:
        words = entity_lower.split()
        acronym = ''.join(w[0] for w in words if len(w) > 2)
        if acronym and acronym in context_lower:
            return True

    return False


def validate_entities(
    answer: str, context_blocks: list[str] | None = None, factual_blocks: list[str] | None = None
) -> list[str]:
    """
    Return entities from answer NOT found in FACTUAL context only.

    """
    entities = extract_entities(answer)
    if not entities:
        return []

    # Use FACTUAL blocks if provided
    # This ensures we ONLY validate against file, memory, web
    # and NEVER against history or follow-up (which are contextual only)
    context_text = None

    if factual_blocks:
        context_text = '\n\n'.join(factual_blocks)
        logger.debug('Using FACTUAL blocks for validation (len=%s)', len(context_text))
    elif context_blocks:
        context_text = '\n\n'.join(context_blocks)
        logger.debug('Using all context blocks for validation (len=%s)', len(context_text))
    else:
        logger.warning('No context blocks provided for entity validation')
        return entities  # All entities are unverified if no context

    if not context_text:
        return entities

    unverified = []
    for entity in entities:
        if not is_entity_in_context(entity, context_text):
            unverified.append(entity)

    logger.debug(
        'Entity validation result: %s total → %s unverified (verified: %s)',
        len(entities),
        len(unverified),
        len(entities) - len(unverified),
        extra={'source': 'entity_validation'},
    )

    return unverified


def assess_factual_guard(unverified: list[str]) -> dict:
    """
    Determine risk level and confidence cap based on unverified entities.
    """
    count = len(unverified)

    if count >= settings.FACTUAL_GUARD_HIGH_UNVERIFIED:
        return {'risk': 'HIGH', 'cap': settings.FACTUAL_GUARD_HIGH_CAP}

    if count >= settings.FACTUAL_GUARD_MED_UNVERIFIED:
        return {'risk': 'MED', 'cap': settings.FACTUAL_GUARD_MED_CAP}

    if count > 0:
        return {'risk': 'LOW', 'cap': settings.FACTUAL_GUARD_LOW_CAP}

    return {'risk': 'NONE', 'cap': 1.0}


def detect_uncertainty(
    source_used: str,
    confidence: float,
    response_text: str,
) -> list[dict]:
    """
    Identify things the assistant might be unsure about.

    """
    flags = []

    # Flag 1: Low confidence in selected source
    if confidence < settings.CONFIDENCE_UNCERTAINTY:
        flags.append(
            {
                'aspect': f'Selected source ({source_used}) has low confidence',
                'confidence': confidence,
                'suggested_actions': ['search_web', 'ask_user'],
            }
        )

    # Flag 2: Uncertainty language in response
    uncertainty_patterns = [
        r'\bmight\b',
        r'\bcould\b',
        r'\bpossibly\b',
        r'\bunclear\b',
        r'\bassume\b',
        r'I\'m not sure',
        r'uncertain',
        r'confusing',
    ]

    if any(re.search(p, response_text, re.IGNORECASE) for p in uncertainty_patterns):
        flags.append(
            {
                'aspect': 'Response contains uncertainty language',
                'confidence': 0.6,
                'suggested_actions': ['search_web', 'ask_user'],
            }
        )

    return flags
