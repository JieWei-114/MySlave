import logging

from fastapi import APIRouter

from app.core.db import rules_collection
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