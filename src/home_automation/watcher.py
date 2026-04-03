import json
import logging
import signal
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers.polling import PollingObserver
from home_automation import downstream

logger = logging.getLogger(__name__)

SUPPORTED_VERSIONS = {1}


class FolderHandler(FileSystemEventHandler):

    def __init__(self, config: dict) -> None:
        self.config = config


    def _handle(self, str_path: str) -> None:
        path = Path(str_path)

        # Route based on filename pattern
        if path.suffix.lower() != ".json":
            return
        if not path.name.startswith("proc_"):
            return
        logger.info("New JSON file detected: %s", path)
        try:
            doc = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to read JSON %s: %s", path.name, e)
            return
        if doc.get("schema_version") not in SUPPORTED_VERSIONS:
            logger.warning("Unknown schema_version in %s, attempting anyway", path.name)
        downstream.process(doc, path.with_suffix(".pdf"), self.config)

    

    
    def on_created(self, event: FileCreatedEvent) -> None:
        self._handle(event.src_path)

    
    def on_modified(self, event: FileModifiedEvent) -> None:
        self._handle(event.src_path)


def start(folder: str, config: dict) -> None:
    handler = FolderHandler(config)
    observer = PollingObserver()
    observer.schedule(handler, str(Path(folder).expanduser()), recursive=True)
    logger.info("Watching: %s", folder)
    observer.start()

    signal.signal(signal.SIGTERM, lambda *_: observer.stop())
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()