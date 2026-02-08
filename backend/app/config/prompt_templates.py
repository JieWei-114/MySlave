"""
Prompt templates and instruction snippets used by chat_service.

"""

# Used in build_prompt_with_memory() when user is following up on previous answer
CONTINUATION_HINT_FOLLOWUP = (
    "Key Follow-up Rules:\n"
    "- Follow-up mode was applied here.\n"
    "- This is a direct follow-up to the PRIMARY CONTEXT.\n"
    "- Only answer specific items or references explicitly requested by the user.\n"
    "- Do not summarize or repeat the entire content of the PRIMARY CONTEXT.\n"
    "- The context only to identify what the user is referring to, not as a source of new facts.\n"
    "- If the cited item is ambiguous or unclear, ask the user for clarification before answering.\n"
    "- If the main context may be incomplete or uncertain, answer carefully and explain its limitations.\n"
    "- Prioritize semantic consistency.\n"
)

# Used in build_context_for_source() when building FILE context block
FILE_CONTEXT_INSTRUCTION = (
    "\n\nIMPORTANT: Read and analyze the above file carefully. Use its contents to answer the user's query."
)

# Used in build_context_for_source() when building HISTORY context block
HISTORY_CONTEXT_HEADER = "CONVERSATION HISTORY. "

# Used in build_context_for_source() when building WEB context block
WEB_CONTEXT_HEADER = "WEB SEARCH RESULTS\nSources: user_query / assistant_context / extracted"

# Used in build_context_for_source() when building MEMORY context block
MEMORY_CONTEXT_HEADER = "RELEVANT MEMORIES"

# Used in build_context_for_source() when building PRIMARY/FOLLOW-UP context
PRIMARY_CONTEXT_HEADER = (
    "PRIMARY CONTEXT — LAST ASSISTANT ANSWER\n"
    "This is the the current question refers to:"
)

# ============================================================
# PHASE 1: INTERNAL REASONING PROMPTS
# ============================================================

# System-level instruction for reasoning phase
REASONING_PHASE_SYSTEM = """
Explain how the answer was produced by mapping directly to the SYSTEM INSTRUCTIONS.
This is a structured justification, not free-form reflection.

1. INTENT INTERPRETATION (STEP 1)
   - Restate how the user’s question was interpreted.
   - Identify the detected intent:
     information / explanation / clarification / continuation.
   - State whether the question was treated as:
     a new question or a follow-up.

2. CONTEXT RESOLUTION (STEP 2)
   - Indicate whether follow-up mode was applied.
   - If yes:
     - Identify the PRIMARY CONTEXT used (previous assistant answer).
     - Explain how vague references or pronouns were resolved.
     - State whether the primary context was sufficient.
   - If no:
     - State that the question was treated as standalone.

3. SOURCE ELIGIBILITY DECISIONS (STEP 3)
   For each source type (FILES / MEMORY / HISTORY / WEB):
   - State the eligibility decision:
     REQUIRED / OPTIONAL / NOT USED.
   - Briefly justify why this classification was chosen.
   - If a REQUIRED source was missing, explain how this affected the answer.

4. SOURCE USAGE & LIMITATIONS (STEP 4)
   For each source actually used:
   - Intended use (factual grounding / support / continuity).
   - What information it contributed.
   - What limitations or uncertainty remained.

5. ANSWER CONSTRUCTION LOGIC (STEP 5)
   - Explain how the final answer was structured.
   - Distinguish:
     - What was answered directly.
     - What was qualified or marked as uncertain.
   - Identify the primary source of truth, if any.

6. CONFIDENCE & VERIFICATION CHECK
   - State why the answer is considered reliable.
   - Explicitly list:
     - Remaining uncertainties.
     - Claims that may require external verification.
   - Note what additional information would increase confidence.

Rules:
- Do not invent reasoning steps that did not occur.
- Do not introduce new facts.
- Use SYSTEM INSTRUCTION terminology consistently.
- If the answer was limited due to missing sources, state this clearly.
"""