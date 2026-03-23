import json
import logging
import subprocess

from cloudflare import Cloudflare

logger = logging.getLogger(__name__)


def _get_token(keychain_service: str) -> str:
    """Read Cloudflare API token from Mac Keychain"""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", keychain_service, "-w"],
        capture_output=True, text=True, check=True
    )

    return result.stdout.strip()


def upsert(doc: dict, account_id: str, database_id: str, keychain_service: str) -> None:
    """Insert or replace a mail_documents record from sidecar JSON."""
    client = Cloudflare(api_token=_get_token(keychain_service))
    client.d1.database.query(
        account_id=account_id,
        database_id=database_id,
        sql="""
            INSERT OR REPLACE INTO mail_documents
            (filename, original_filename, date, issued, sender, reference, type,
            importance, amount, deadline, action_items, summary_short,
            ocr_confidence, deepl_score, claude_confidence, tokens_in, tokens_out,
            cost_usd, model, schema_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        params = [
            doc.get("filename"), doc.get("original_filename"), doc.get("date"),
            doc.get("issued"), doc.get("sender"), doc.get("reference"), doc.get("type"),
            doc.get("importance"), doc.get("amount"), doc.get("deadline"),
            json.dumps(doc.get("action_items", [])), doc.get("summary_short"),
            doc.get("ocr_confidence"), doc.get("deepl_score"), doc.get("claude_confidence"),
            doc.get("tokens_in"), doc.get("tokens_out"), doc.get("cost_usd"),
            doc.get("model"), doc.get("schema_version"), doc.get("date"),
        ]
    )
    
    logger.info("D1 upsert OK: %s", doc.get("filename"))
