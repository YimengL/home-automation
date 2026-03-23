import logging


logger = logging.getLogger(__name__)


def process(doc: dict) -> None:
    logger.info("downstream.process called: %s", doc.get("filename"))
