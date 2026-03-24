import logging

from pathlib import Path
from home_automation import d1, r2, telegram


logger = logging.getLogger(__name__)


def process(doc: dict, pdf_path: Path, config: dict) -> None:
    cf = config["cloudflare"]
    r2_cfg = config["r2"]
    tg = config["telegram"]

    # D1 upsert
    d1.upsert(
        doc,
        account_id=cf["account_id"],
        database_id=cf["d1_database_id"],
        keychain_service=cf["api_token_keychain_service"],
    )

    # R2 upload
    key = r2.upload(
        pdf_path, doc, account_id=cf["account_id"],
        bucket_name=r2_cfg["bucket_name"],
        key_id_service=r2_cfg["key_id_keychain_service"],
        secret_service=r2_cfg["secret_keychain_service"],
    )

    # Presign + Telegram
    presigned_url = r2.presign(key, account_id=cf["account_id"],
                               bucket_name=r2_cfg["bucket_name"],
                               key_id_service=r2_cfg["key_id_keychain_service"],
                               secret_service=r2_cfg["secret_keychain_service"])
    
    telegram.send(doc, presigned_url, chat_id=tg["chat_id"], keychain_service=tg["bot_token_keychain_service"])
