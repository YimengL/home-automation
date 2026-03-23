import argparse
import logging
import signal
import json
import subprocess
import tomllib
from pathlib import Path


from home_automation import pdf_watcher, json_watcher, downstream


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load watched folder config from ~/.config/home-automation/config.toml"""
    config_path = Path("~/.config/home-automation/config.toml").expanduser()
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def cmd_watch_pdf(folders: list[str], translate_bin: str) -> None:
    observer = pdf_watcher.start(folders, translate_bin)
    # Graceful shutdown: launchd sends SIGTERM, terminal sends KeyboardInterrupt
    signal.signal(signal.SIGTERM, lambda *_: observer.stop())
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()


def cmd_watch_json(folders: list[str], config: dict) -> None:
    observer = json_watcher.start(folders, config)
    signal.signal(signal.SIGTERM, lambda *_: observer.stop())
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()


def cmd_retranslate(pdf_path: str, translate_bin: str) -> None:
    """Run translate directly on a PDF, bypassing the watchdog."""
    subprocess.run([translate_bin, pdf_path], check=True)


def cmd_reingest(json_path: str, config: dict) -> None:
    """Run downstream directly on a proc_*.json, bypassing the watchdog."""
    doc = json.loads(Path(json_path).read_text())
    downstream.process(doc, config)


def main() -> None:
    parser = argparse.ArgumentParser(prog="home-automation")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("watch-pdf")
    sub.add_parser("watch-json")

    p = sub.add_parser("retranslate")
    p.add_argument("pdf_path")

    p = sub.add_parser("reingest")
    p.add_argument("json_path")

    args = parser.parse_args()
    config = load_config()
    folders = [f["path"] for f in config["watched_folders"]]
    translate_bin = config["translate"]["bin"]

    if args.cmd == "watch-pdf":
        cmd_watch_pdf(folders, translate_bin)
    elif args.cmd == "watch-json":
        cmd_watch_json(folders, config)
    elif args.cmd == "retranslate":
        cmd_retranslate(args.pdf_path, translate_bin)
    elif args.cmd == "reingest":
        cmd_reingest(args.json_path, config)
