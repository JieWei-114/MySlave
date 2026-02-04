import json
import logging
import re
import uuid
from datetime import datetime

from app.config.settings import settings
from app.core.db import sessions_collection
from app.services.memory_service import (
    delete_memories_for_session,
    search_memories,
    auto_memory_if_needed,
)
from app.services.ollama_service import call_ollama_once, stream_ollama
from app.services.web_search_service import maybe_extract, maybe_web_search

logger = logging.getLogger(__name__)


# Centralized limits from settings (defaults)
PROMPT_MAX_TOTAL = settings.CHAT_PROMPT_MAX_TOTAL_CHARS

# History
HISTORY_LIMIT = settings.CHAT_HISTORY_LIMIT
HISTORY_MAX_PER_MSG = settings.CHAT_HISTORY_MAX_CHARS_PER_MSG
HISTORY_TOTAL_MAX = settings.CHAT_HISTORY_TOTAL_MAX_CHARS
MAX_ASSISTANT_CONTEXT = settings.CHAT_HISTORY_MAX_ASSISTANT_CONTEXT

# Memory
MEMORY_RESULTS_LIMIT = settings.CHAT_MEMORY_RESULTS_LIMIT
MEMORY_TOTAL_MAX = settings.CHAT_MEMORY_TOTAL_MAX_CHARS

# Web search
WEB_RESULTS_LIMIT = settings.CHAT_WEB_RESULTS_LIMIT
WEB_SNIPPET_MAX = settings.CHAT_WEB_SNIPPET_MAX_CHARS
WEB_TOTAL_MAX = settings.CHAT_WEB_TOTAL_MAX_CHARS

# URL extraction
EXTRACT_TOTAL_MAX = settings.CHAT_EXTRACT_TOTAL_MAX_CHARS

# File upload
FILE_CONTENT_MAX = settings.CHAT_FILE_CONTENT_MAX_CHARS

# Features
ENABLE_RANKING = settings.CHAT_ENABLE_RESULT_RANKING
SYSTEM_INSTRUCTIONS = settings.CHAT_SYSTEM_INSTRUCTIONS

# ============================================================
# Session CRUD
# ============================================================


def create_session(title: str) -> dict:
    now = datetime.utcnow()

    session = {
        'id': str(uuid.uuid4()),
        'title': title,
        'messages': [],
        'created_at': now,
        'updated_at': now,
        'rules': {
            'searxng': True,
            'duckduckgo': True,
            'tavily': False,
            'serper': False,
            'tavilyExtract': False,
            'localExtract': True,
        },
    }

    sessions_collection.insert_one(session)

    return {
        'id': session['id'],
        'title': session['title'],
        'messages': [],
        'created_at': session['created_at'],
        'updated_at': session['updated_at'],
        'rules': session['rules'],
    }


def get_session(session_id: str) -> dict | None:
    session = sessions_collection.find_one({'id': session_id}, {'_id': 0, 'pending_attachment': 0})
    return session


def get_session_rules(session_id: str) -> dict:
    """Get session-specific rules. Always returns a dict."""
    try:
        session = sessions_collection.find_one(
            {'id': session_id},
            {'_id': 0, 'rules': 1},
        )
        return session.get('rules', {}) if session else {}
    except Exception as e:
        logger.error(f'Error fetching session rules for {session_id}: {e}')
        return {}


def list_sessions() -> list[dict]:
    cursor = sessions_collection.find(
        {'id': {'$ne': '__order__'}},
        {
            '_id': 0,
            'id': 1,
            'title': 1,
            'updated_at': 1,
        },
    )

    sessions = list(cursor)

    order_doc = sessions_collection.find_one({'id': '__order__'}, {'_id': 0})
    if order_doc and 'sessionIds' in order_doc:
        ordered_ids = order_doc['sessionIds']
        session_map = {s['id']: s for s in sessions}

        result = []
        for sid in ordered_ids:
            if sid in session_map:
                result.append(session_map[sid])

        for s in sessions:
            if s['id'] not in ordered_ids:
                result.append(s)

        return result

    return sorted(sessions, key=lambda s: s.get('updated_at', ''), reverse=True)


def rename_session(session_id: str, title: str) -> dict:
    result = sessions_collection.update_one(
        {'id': session_id}, {'$set': {'title': title, 'updated_at': datetime.utcnow()}}
    )

    if result.matched_count == 0:
        return None

    return {'id': session_id, 'title': title}


def delete_session(session_id: str) -> bool:
    result = sessions_collection.delete_one({'id': session_id})
    if result.deleted_count != 1:
        return False

    sessions_collection.update_one(
        {'id': '__order__'},
        {'$pull': {'sessionIds': session_id}},
    )

    # delete any memories tied to this chat session
    delete_memories_for_session(session_id)
    return True


# ============================================================
# File / Attachment Handling
# ============================================================


def extract_key_points(text: str, max_points: int = 5) -> list[str]:
    """
    Extract key points/sentences from extracted content for smart web search.
    Used to generate intelligent search queries based on extracted page content.

    """
    if not text or len(text) < 100:
        return []

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if not sentences:
        return []

    # Score sentences by position + length
    scored = []
    for idx, sent in enumerate(sentences[:30]):  # Check first 30 sentences
        position_weight = 1.0 / (idx + 1)  # Earlier = more important
        length_weight = min(len(sent) / 150, 1.0)  # Longer = more info
        score = position_weight * 0.6 + length_weight * 0.4
        scored.append((score, sent))

    scored.sort(key=lambda x: x[0], reverse=True)
    key_points = [s[1] for s in scored[:max_points]]

    logger.debug(f'Extracted {len(key_points)} key points from content')
    return key_points


def pop_pending_attachment(session_id: str) -> dict | None:
    """Fetch and clear pending attachment for a session (one-time use)."""
    try:
        session = sessions_collection.find_one(
            {'id': session_id},
            {'_id': 0, 'pending_attachment': 1},
        )
        attachment = session.get('pending_attachment') if session else None
        if attachment:
            sessions_collection.update_one(
                {'id': session_id},
                {'$unset': {'pending_attachment': ''}},
            )
        return attachment
    except Exception as e:
        logger.warning(f'Failed to retrieve pending attachment: {e}')
        return None


# ============================================================
# NLP / Search Utilities
# ============================================================


def extract_file_content(user_content: str) -> tuple[str, dict | None]:
    """
    Extract uploaded file content from user message.
    Returns: (cleaned_message, file_info_dict or None)
    """
    if not user_content:
        return user_content, None

    # Pattern: [Attached file: filename.ext]\nfile_content
    pattern = r'\n\n\[Attached file: ([^\]]+)\]\n(.+)'
    match = re.search(pattern, user_content, re.DOTALL)

    if not match:
        return user_content, None

    filename = match.group(1)
    file_content = match.group(2)

    # Remove file section from message
    clean_message = user_content[: match.start()].strip()

    file_info = {
        'filename': filename,
        'content': file_content,
        'length': len(file_content),
        'type': 'unknown',
    }

    # Detect file type from extension
    if filename.lower().endswith('.pdf'):
        file_info['type'] = 'PDF'
    elif filename.lower().endswith(('.docx', '.doc')):
        file_info['type'] = 'Word'
    elif filename.lower().endswith(('.txt', '.md')):
        file_info['type'] = 'Text'
    elif filename.lower().endswith(('.json', '.yaml', '.yml')):
        file_info['type'] = 'Config'
    elif filename.lower().endswith(('.py', '.js', '.ts', '.java', '.cpp')):
        file_info['type'] = 'Code'

    return clean_message, file_info


def rank_search_results(results: list[dict], query: str) -> list[dict]:
    """
    Rank search results by relevance to query.
    Uses simple keyword matching scoring.
    """
    if not ENABLE_RANKING or not results:
        return results

    query_terms = set(query.lower().split())
    # Remove common words that don't add relevance
    stop_words = {
        'the',
        'a',
        'an',
        'and',
        'or',
        'but',
        'in',
        'on',
        'at',
        'to',
        'for',
        'of',
        'with',
        'by',
    }
    query_terms = query_terms - stop_words

    if not query_terms:
        return results

    scored = []
    for r in results:
        # Score based on title + snippet content
        title = r.get('title', '').lower()
        snippet = r.get('snippet', '').lower()
        content = snippet

        text = f'{title} {title} {content}'  # Weight title 2x

        # Count term matches
        score = sum(1 for term in query_terms if term in text)

        # Boost score if terms appear in title
        title_boost = sum(2 for term in query_terms if term in title)

        total_score = score + title_boost
        scored.append((total_score, r))

    # Sort by score descending, keep original order for ties
    scored.sort(key=lambda x: x[0], reverse=True)

    return [r for _, r in scored]


def build_search_candidates(
    user_content: str,
    primary_assistant_answer: str | None,
    extracted_key_points: list[str],
    extracted: bool,
    is_followup: bool,
) -> list[dict]:
    """
    Build multiple search candidates for web search.
    Returns list of { query, source }.
    """
    candidates: list[dict] = []

    # 1. Extracted key points
    if extracted and extracted_key_points:
        candidates.append({
            'query': extracted_key_points[0],
            'source': 'extracted',
        })

    # 2. user current content
    candidates.append({
        'query': user_content,
        'source': 'user_query',
    })

    # 3. Follow-up content
    if is_followup and primary_assistant_answer:
        candidates.append({
            'query': primary_assistant_answer[:300],
            'source': 'assistant_context',
        })

    return candidates


# ============================================================
# Prompt & Context Construction
# ============================================================


async def build_prompt_with_memory(
    user_content: str,
    chat_sessionId: str = 'default',
) -> tuple[str, str]:
    
    if not user_content or not user_content.strip():
        return '', ''

    user_content = user_content.strip()
    logger.info('Build prompt start', extra={'session_id': chat_sessionId})
    logger.info(
        'User query received (len=%s)',
        len(user_content),
        extra={'session_id': chat_sessionId},
    )

    # Get session-specific rules (limits + instructions)
    session_rules = get_session_rules(chat_sessionId)

    # Use custom limits if set in rules, otherwise use settings defaults
    local_web_limit = (
        session_rules.get('webSearchLimit') if session_rules else None
    ) or WEB_RESULTS_LIMIT
    local_history_limit = (
        session_rules.get('historyLimit') if session_rules else None
    ) or HISTORY_LIMIT
    local_memory_limit = (
        session_rules.get('memorySearchLimit') if session_rules else None
    ) or MEMORY_RESULTS_LIMIT
    local_file_limit = (
        session_rules.get('fileUploadMaxChars') if session_rules else None
    ) or FILE_CONTENT_MAX
    custom_instructions = (
        session_rules.get('customInstructions', '') if session_rules else ''
    ) or ''

    # Build system instructions with custom rules
    system_instructions = SYSTEM_INSTRUCTIONS
    if custom_instructions:
        system_instructions += f'\n\nCUSTOM SESSION INSTRUCTIONS:\n{custom_instructions}'
        logger.info(
            'Custom session instructions applied (len=%s)',
            len(custom_instructions),
            extra={'session_id': chat_sessionId},
        )

    # Extract file content if present in message
    clean_message, file_info = extract_file_content(user_content)
    user_content = clean_message if file_info else user_content

    # Fallback to pending attachment (uploaded separately)
    if not file_info:
        logger.info('Checking for pending attachment...', extra={'session_id': chat_sessionId})
        pending = pop_pending_attachment(chat_sessionId)
        logger.info(
            'pop_pending_attachment returned: %s',
            'YES (file present)' if pending else 'NO (no pending file)',
            extra={'session_id': chat_sessionId},
        )
        if pending:
            file_info = pending
            logger.info(
                'Pending attachment loaded: %s',
                pending.get('filename'),
                extra={'session_id': chat_sessionId},
            )

    if file_info:
        logger.info(
            'File attached: %s (%s, %s chars)',
            file_info.get('filename'),
            file_info.get('type'),
            file_info.get('length'),
            extra={'session_id': chat_sessionId},
        )

    blocks: list[str] = []
    metadata = {
        'memory_count': 0,
        'memory_sources': [],
        'web_count': 0,
        'web_sources': set(),
        'extracted': False,
        'extracted_key_points': [],
        'file_attached': file_info is not None,
    }
    history_used = False
    web_used = False
    memory_used = False
    extracted_used = False
    file_used = False

    # 1. Conversation History

    primary_assistant_answer = None
    secondary_assistant_answers: list[str] = []

    try:
        session = sessions_collection.find_one(
            {'id': chat_sessionId},
            {'_id': 0, 'messages': 1},
        )
        if session and session.get('messages'):
            msgs = session['messages']

            # extract last assistant message (most important)

            assistant_answers = []

            for m in reversed(msgs):
                if m['role'] == 'assistant' and m.get('content'):
                    assistant_answers.append(m['content'])
                    if len(assistant_answers) >= MAX_ASSISTANT_CONTEXT:
                        break

            if assistant_answers:
                primary_assistant_answer = assistant_answers[0]
                secondary_assistant_answers = assistant_answers[1:]

            # normal conversation history 
            recent_messages = session['messages'][-local_history_limit:]

            if recent_messages:
                history_lines = []
                for msg in recent_messages:
                    role = msg['role'].upper()
                    content = msg['content']
                    if len(content) > HISTORY_MAX_PER_MSG:
                        content = content[:HISTORY_MAX_PER_MSG] + '...'
                    history_lines.append(f'{role}: {content}')

                blocks.append('CONVERSATION HISTORY\n' + '\n\n'.join(history_lines))
                history_used = True
                logger.info(
                    'History added (%s messages, limit=%s, total_chars=%s)',
                    len(recent_messages),
                    local_history_limit,
                    sum(len(m.get('content', '')) for m in recent_messages),
                    extra={'session_id': chat_sessionId},
                )

                role_stats = {'user': 0, 'assistant': 0}
                for m in recent_messages:
                    role_stats[m['role']] += 1
                logger.info(
                    "History composition: total=%s, user=%s, assistant=%s",
                    len(recent_messages),
                    role_stats['user'],
                    role_stats['assistant'],
                    extra={'session_id': chat_sessionId},
                )
    except Exception as e:
        logger.warning(f'Failed to retrieve conversation history: {e}')

    # insert assistant anchors
    if primary_assistant_answer:
        blocks.insert(
            0,
            "PRIMARY CONTEXT — LAST ASSISTANT ANSWER (AUTHORITATIVE)\n"
            "This is the main answer the current question refers to:\n\n"
            + primary_assistant_answer
        )

        logger.info(
            "Follow-up detected. "
            "Primary assistant answer preview: %s",
            primary_assistant_answer[:200].replace('\n', ' ') + '...',
            extra={'session_id': chat_sessionId},
        )

    if secondary_assistant_answers:
        blocks.insert(
            1,
            "SECONDARY CONTEXT — RECENT ASSISTANT ANSWERS (BACKGROUND)\n"
            "These provide additional context leading to the primary answer:\n\n"
            + "\n\n---\n\n".join(secondary_assistant_answers)
        )

        logger.info(
            "Assistant context analysis: "
            "primary_present=%s, secondary_count=%s",
            bool(primary_assistant_answer),
            len(secondary_assistant_answers),
            extra={'session_id': chat_sessionId},
        )

    # Follow-up control
    is_followup = False
    continuation_hint = ''

    if primary_assistant_answer:
        is_followup = True
        continuation_hint = (
            "CRITICAL CONTEXT RULE (MUST FOLLOW):\n"
            "- The user's question is a DIRECT FOLLOW-UP to the PRIMARY ASSISTANT ANSWER.\n"
            "- DO NOT start a new topic.\n"
            "- PRIORITIZE PRIMARY CONTEXT over history, memory, or web.\n\n"
        )

        # down-rank distractions
        local_memory_limit = min(local_memory_limit, 3)
        # local_web_limit = min(local_web_limit, 3)

    # 2. URL EXTRACTION & KEY POINT ANALYSIS
    extracted_content = None
    extracted_key_points = []

    try:
        extracted_content = await maybe_extract(user_content, session_id=chat_sessionId)

        if extracted_content and extracted_content.strip():
            metadata['extracted'] = True
            extracted_used = True

            # Show extracted content to user
            display_content = extracted_content
            if len(display_content) > EXTRACT_TOTAL_MAX:
                display_content = display_content[:EXTRACT_TOTAL_MAX] + '\n\n[Truncated]'

            blocks.append('EXTRACTED WEB CONTENT\n' + display_content)
            logger.info(
                'URL extraction added (chars=%s, truncated=%s)',
                len(display_content),
                len(display_content) < len(extracted_content),
                extra={'session_id': chat_sessionId},
            )

            # Analyze: extract key points for smart web search
            extracted_key_points = extract_key_points(extracted_content, max_points=3)
            metadata['extracted_key_points'] = extracted_key_points

            logger.info(
                'Key points extracted (%s): %s',
                len(extracted_key_points),
                extracted_key_points,
                extra={'session_id': chat_sessionId},
            )
    except Exception as e:
        logger.warning(f'Failed to extract URL content: {e}')

    # 3. MULTI-SOURCE WEB SEARCH (user + assistant + extracted)
    try:
        search_candidates = build_search_candidates(
            user_content=user_content,
            primary_assistant_answer=primary_assistant_answer,
            extracted_key_points=extracted_key_points,
            extracted=metadata['extracted'],
            is_followup=is_followup,
        )

        logger.info(
            'Web search candidates: %s',
            [(c['source'], c['query'][:80]) for c in search_candidates],
            extra={'session_id': chat_sessionId},
        )

        all_results: list[dict] = []
        seen_urls: set[str] = set()

        # candidate search
        per_candidate_limit = max(3, local_web_limit // len(search_candidates))

        for candidate in search_candidates:
            try:
                results = await maybe_web_search(
                    query=candidate['query'],
                    session_id=chat_sessionId,
                )

                results = results[:per_candidate_limit]
            except Exception as e:
                logger.warning(
                    'Web search failed for %s: %s',
                    candidate['source'],
                    e,
                    extra={'session_id': chat_sessionId},
                )
                continue

            for r in results:
                url = r.get('link')
                if not url or url in seen_urls:
                    continue

                r['_from'] = candidate['source']
                all_results.append(r)
                seen_urls.add(url)

                if len(all_results) >= local_web_limit * 2:
                    break

            if len(all_results) >= local_web_limit * 2:
                break

        if all_results:
            ranked_results = rank_search_results(all_results, user_content)
            final_results = ranked_results[:local_web_limit]

            web_lines = []
            total_chars = 0

            for r in final_results:
                source = r.get('source', 'unknown').upper()
                metadata['web_sources'].add(source)

                title = r.get('title', '')
                snippet = r.get('snippet', '')
                display_text = snippet

                if len(display_text) > WEB_SNIPPET_MAX:
                    display_text = display_text[:WEB_SNIPPET_MAX] + '...'

                origin = r.get('_from', 'unknown')
                result_text = f'[{source}] ({origin}) {title}\n{display_text}'

                if total_chars + len(result_text) > WEB_TOTAL_MAX:
                    break

                web_lines.append(result_text)
                total_chars += len(result_text)

            metadata['web_count'] = len(web_lines)

            if web_lines:
                blocks.append(
                    'WEB SEARCH RESULTS\n'
                    'Sources: user_query / assistant_context / extracted\n\n'
                    + '\n\n'.join(web_lines)
                )
                web_used = True

                logger.info(
                    'Web results added (%s results, sources=%s)',
                    len(web_lines),
                    sorted(metadata['web_sources']),
                    extra={'session_id': chat_sessionId},
                )

                logger.info(
                    'Web sources summary: %s',
                    [
                        {
                            'source': r.get('source', '').upper(),
                            'from': r.get('_from'),
                            'title': r.get('title'),
                            'link': r.get('link'),
                        }
                        for r in final_results
                    ],
                    extra={'session_id': chat_sessionId},
                )
        else:
            logger.info(
                'Web search returned no results',
                extra={'session_id': chat_sessionId},
            )

    except Exception as e:
        logger.warning(f'Failed to perform web search: {e}')

    # 4. SEMANTIC MEMORY SEARCH
    try:
        memory_query = primary_assistant_answer if is_followup else user_content

        memories = search_memories(
            chat_sessionId=chat_sessionId, query=memory_query, limit=local_memory_limit
        )

        if memories:
            memory_lines = []
            total_chars = 0

            for m in memories:
                content = m.get('content', '')

                if total_chars + len(content) > MEMORY_TOTAL_MAX:
                    break

                src = m.get('source', 'manual')
                metadata['memory_sources'].append(src)
                memory_lines.append(f'[{src.upper()}] {content}')
                total_chars += len(content)

            metadata['memory_count'] = len(memory_lines)

            if memory_lines:
                blocks.append('RELEVANT MEMORIES\n' + '\n\n'.join(memory_lines))
                memory_used = True
                logger.info(
                    'Memories added (%s items, limit=%s)',
                    len(memory_lines),
                    local_memory_limit,
                    extra={'session_id': chat_sessionId},
                )
                logger.info(
                    'Memory sources summary: %s',
                    sorted(set(metadata['memory_sources'])),
                    extra={'session_id': chat_sessionId},
                )
        else:
            logger.info(
                'No memories matched',
                extra={'session_id': chat_sessionId},
            )
    except Exception as e:
        logger.warning(f'Failed to retrieve persistent memories: {e}')

    # 5. FILE UPLOAD CONTENT
    if file_info:
        try:
            file_content = file_info['content']
            if len(file_content) > local_file_limit:
                file_content = file_content[:local_file_limit] + '\n\n[Truncated]'

            # Format file with clear markers so model knows to analyze it
            file_section = f"""UPLOADED FILE: {file_info['filename']}
File Type: {file_info['type']}
Content Length: {len(file_content)} characters

---BEGIN FILE CONTENT---
{file_content}
---END FILE CONTENT---

IMPORTANT: Read and analyze the above file carefully. Use its contents to answer the user's query. The user may ask questions about this file or want you to analyze/summarize it."""

            blocks.append(file_section)
            file_used = True
            logger.info(
                'File content added (chars=%s, truncated=%s)',
                len(file_content),
                len(file_content) < len(file_info['content']),
                extra={'session_id': chat_sessionId},
            )
        except Exception as e:
            logger.warning(f'Failed to add file content: {e}')

    # 6. Build final prompt
    summary_header = f"""CONTEXT SUMMARY
Query: {user_content[:100]}{'...' if len(user_content) > 100 else ''}
File: {'YES' if file_info else 'NO'}
Memory: {metadata['memory_count']} items
Web: {metadata['web_count']} results ({', '.join(sorted(metadata['web_sources'])) if metadata['web_sources'] else 'none'})
Extracted: {'YES' if metadata['extracted'] else 'NO'}"""

    context = '\n\n'.join(blocks) if blocks else 'No augmented context available.'

    prompt = f"""{continuation_hint}

{'=' * 80}

{summary_header}

{'=' * 80}

{context}

{'=' * 80}

USER QUERY: {user_content}

A:
"""

    if len(prompt) > PROMPT_MAX_TOTAL:
        prompt = prompt[:PROMPT_MAX_TOTAL] + '\n\n[Truncated]'

    logger.info(
        'Sources used summary: history=%s, web=%s, memories=%s, web_used=%s, memory_used=%s, extracted=%s, file=%s',
        history_used,
        sorted(metadata['web_sources']) if metadata['web_sources'] else [],
        sorted(set(metadata['memory_sources'])) if metadata['memory_sources'] else [],
        web_used,
        memory_used,
        extracted_used,
        file_used,
        extra={'session_id': chat_sessionId},
    )
    logger.info(
        'Prompt built: total_chars=%s, metadata=%s',
        len(prompt),
        metadata,
        extra={'session_id': chat_sessionId},
    )
    return system_instructions, prompt


# ============================================================
# Core Streaming Chat Logic
# ============================================================


async def stream_chat_reply(session_id: str, content: str, model: str):
    """
    Dual-phase assistant generation:
    1. Internal reasoning (non-streamed, saved to meta.reasoning)
    2. Final answer (streamed to client, saved to content)
    """

    # ------------------------------------------------------------
    # 1. Save USER message
    # ------------------------------------------------------------
    sessions_collection.update_one(
        {'id': session_id},
        {
            '$push': {
                'messages': {
                    'role': 'user',
                    'content': content,
                    'created_at': datetime.utcnow(),
                }
            },
            '$set': {'updated_at': datetime.utcnow()},
        },
    )

    # ------------------------------------------------------------
    # 2️. Build augmented prompt
    # ------------------------------------------------------------
    system_prompt, final_prompt = await build_prompt_with_memory(
        user_content=content,
        chat_sessionId=session_id,
    )

    # ------------------------------------------------------------
    # 3️. Phase 1 — INTERNAL REASONING (no streaming)
    # ------------------------------------------------------------
    reasoning_prompt = """
You are performing internal analysis.

Rules:
- Think silently and concisely.
- Do NOT answer the user.
- Do NOT include explanations or formatting.
- Do NOT repeat the question.
- Output plain internal notes only.
"""

    reasoning_input = f"""
You are analyzing the user's intent and relevant context.

USER QUERY:
{content}

Return ONLY internal reasoning notes.
"""

    try:
        reasoning = await call_ollama_once(
            prompt=reasoning_input,
            model=model,
            system=system_prompt + '\n\n' + reasoning_prompt,
        )
    except Exception as e:
        logger.error('Reasoning generation failed: %s', e)
        reasoning = None

    # ------------------------------------------------------------
    # 4️. Phase 2 — FINAL ANSWER (streamed)
    # ------------------------------------------------------------
    answer_prompt = f"""
INTERNAL REASONING (DO NOT REPEAT):
{reasoning or ''}

----------------------------
If the user's request is ambiguous, incomplete, or underspecified:

1. First, briefly explain what you DO understand from the user's message.
2. Clearly state what information is missing or unclear.
3. Ask specific clarification questions.
4. Do NOT guess missing details.
5. If no safe answer can be given, say you do not have enough information yet.

You are allowed to say:
- "I’m not sure yet"
- "I may be missing some information"
- "Could you clarify ......"

Now provide the FINAL answer to the user.
Be clear, concise, and helpful.
"""

    assistant_answer = ''

    try:
        async for token in stream_ollama(
            prompt=final_prompt,
            model=model,
            system=system_prompt + '\n\n' + answer_prompt,
        ):
            assistant_answer += token
            yield json.dumps({ "type": "token", "data": token })

    except Exception as e:
        logger.error('Answer streaming failed: %s', e)
        yield json.dumps({
            "type": "error",
            "message": "Error generating response"
        })
        return

    # ------------------------------------------------------------
    # 5. Persist ASSISTANT message
    # ------------------------------------------------------------
    if reasoning and len(reasoning) > 2000:
        reasoning = reasoning[:2000] + '\n[truncated]'

    assistant_message = {
        'role': 'assistant',
        'content': assistant_answer.strip(),
        'created_at': datetime.utcnow(),
        'meta': {
            'reasoning': reasoning,
            'citations': None,
            'tools_used': None,
        },
    }

    sessions_collection.update_one(
        {'id': session_id},
        {
            '$push': {'messages': assistant_message},
            '$set': {'updated_at': datetime.utcnow()},
        },
    )

    # ------------------------------------------------------------
    # 6. AUTO MEMORY (non-blocking)
    # ------------------------------------------------------------
    try:
        await auto_memory_if_needed(
            chat_sessionId=session_id,
            user_text=content,
            assistant_text=assistant_answer,
            model=model,
        )
    except Exception as e:
        logger.error('Auto memory failed: %s', e)

    # ------------------------------------------------------------
    # 7. End SSE
    # ------------------------------------------------------------
    yield json.dumps(
        {
            'type': 'done',
            'reasoning': reasoning or "",
        }
    )
