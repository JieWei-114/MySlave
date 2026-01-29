import logging

from fastapi import APIRouter

from app.core.db import rules_collection, sessions_collection
from app.models.dto import RulesConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/rules', tags=['rules'])


@router.get('', response_model=RulesConfig)
async def get_rules():
    try:
        rules = rules_collection.find_one({}, {'_id': 0})

        if not rules:
            default_rules = RulesConfig()
            return default_rules

        return RulesConfig(**rules)

    except Exception as e:
        logger.error(f'Error fetching rules: {e}')
        return RulesConfig()


@router.put('', response_model=RulesConfig)
async def update_rules(rules: RulesConfig):
    try:
        rules_dict = rules.model_dump()
        rules_collection.update_one({}, {'$set': rules_dict}, upsert=True)
        logger.info(f'Rules updated: {rules_dict}')
        return rules

    except Exception as e:
        logger.error(f'Error updating rules: {e}')
        raise


@router.get('/{session_id}', response_model=RulesConfig)
async def get_session_rules(session_id: str):
    try:
        session = sessions_collection.find_one({'id': session_id}, {'_id': 0})

        if not session:
            logger.warning(f'Session not found: {session_id}')
            return RulesConfig()

        rules = session.get('rules', {})
        logger.debug(f'Retrieved rules for session {session_id}: {rules}')
        return RulesConfig(**rules) if rules else RulesConfig()

    except Exception as e:
        logger.error(f'Error fetching session rules: {e}')
        return RulesConfig()


@router.put('/{session_id}', response_model=RulesConfig)
async def update_session_rules(session_id: str, rules: RulesConfig):
    try:
        # Convert RulesConfig to dict for MongoDB storage
        rules_dict = rules.model_dump()
        logger.info(f'Updating session rules for {session_id} with: {rules_dict}')

        result = sessions_collection.update_one(
            {'id': session_id},
            {'$set': {'rules': rules_dict}},
        )

        logger.info(
            f'Update result - matched: {result.matched_count}, modified: {result.modified_count}'
        )

        if result.matched_count == 0:
            logger.warning(f'Session not found: {session_id}')
            raise ValueError('Session not found')

        if result.modified_count == 0:
            logger.warning(f'No changes made to session {session_id}')

        logger.info(f'Session rules updated for {session_id}: {rules_dict}')

        # Verify the update by reading back
        updated_session = sessions_collection.find_one({'id': session_id}, {'_id': 0})
        logger.info(
            f'Verification - Updated session rules from DB: {updated_session.get("rules") if updated_session else "Session not found"}'
        )

        return rules

    except Exception as e:
        logger.error(f'Error updating session rules: {e}')
        raise
