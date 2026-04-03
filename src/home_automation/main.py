import argparse
import logging

import json
import os
import subprocess
from pathlib import Path


from home_automation import downstream, watcher


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def build_config() -> dict:
    return {
        "cloudflare": {
            "account_id": os.environ["CF_ACCOUNT_ID"],
            "d1_database_id": os.environ["CF_D1_DATABASE_ID"],
            "api_token_keychain_service": "cloudflare-home-automation",
        },
        "r2": {
            "bucket_name": os.environ["R2_BUCKET_NAME"],
            "key_id_keychain_service": "r2-home-automation-mail-key-id",
            "secret_keychain_service": "r2-home-automation-mail-secret",
        },
        "telegram": {
            "chat_id": os.environ["TG_CHAT_ID"],
            "bot_token_keychain_service": "ym_mail_bot",
        }
    }


def cmd_retranslate(pdf_path: str) -> None:
    """Run translate directly on a PDF, bypassing the watchdog."""
    subprocess.run(["/usr/local/bin/translate", pdf_path], check=True)


def cmd_reprocess(json_path) -> None:
    path = Path(json_path)
    doc = json.loads(path.read_text())
    downstream.process(doc, path.with_suffix(".pdf"), build_config())


def main() -> None:
    parser = argparse.ArgumentParser(prog="home-automation")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("watch")
    p.add_argument("folder", nargs="?", default=os.environ.get("WATCH_FOLDER"))

    p = sub.add_parser("retranslate")
    p.add_argument("pdf_path")

    p = sub.add_parser("reprocess")
    p.add_argument("json_path")

    args = parser.parse_args()

    if args.cmd == "watch":
        if not args.folder:
            parser.error("folder argument or WATCH_FOLDER env var is required")
        watcher.start(args.folder, build_config())
    elif args.cmd == "retranslate":
        cmd_retranslate(args.pdf_path)
    elif args.cmd == "reprocess":
        cmd_reprocess(args.json_path)
