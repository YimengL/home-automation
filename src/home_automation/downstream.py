import logging
from home_automation import d1


logger = logging.getLogger(__name__)


def process(doc: dict, config: dict) -> None:
    cf = config["cloudflare"]
    d1.upsert(
        doc,
        account_id=cf["account_id"],
        database_id=cf["d1_database_id"],
        keychain_service=cf["api_token_keychain_service"],
    )
    logger.info("downstream.process called: %s", doc.get("filename"))
