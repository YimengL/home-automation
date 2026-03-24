import logging
import requests

from home_automation import keychain

logger = logging.getLogger(__name__)


def _format_message(doc: dict, presigned_url: str) -> str:
    """Format Telegram notification from sidecar JSON."""
    importance = doc.get("importance", 0)
    if importance >= 80:
        emoji = "🔴"
    elif importance >= 60:
        emoji = "🟡"
    elif importance >= 30:
        emoji = "🟢"
    else:
        emoji = "⚪"
    
    lines = [
        "📬 New mail processed",
        "",
        f"From: {doc.get('sender', 'Unknown')}",
        f"Type: {doc.get('type', 'Unknown')}",
        "",
        f"{emoji} {importance}/100",
    ]
    if doc.get("amount"):
        lines.append(f"💰 {doc['amount']}")
    if doc.get("deadline"):
        lines.append(f"📅 Due: {doc['deadline']}")
    if doc.get("summary_short"):
        lines.append(f"\n{doc['summary_short']}")
    lines.append(f"\n📄 [View PDF]({presigned_url})")
    return "\n".join(lines)


def send(doc: dict, presigned_url: str, chat_id: str, keychain_service: str) -> None:
    """Send Telegram notification for a processed mail document."""
    token = keychain.get_token(keychain_service)
    text = _format_message(doc, presigned_url)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    resp.raise_for_status()
    logger.info("Telegram sent: %s", doc.get("filename"))
