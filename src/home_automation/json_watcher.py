import json
import logging
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer
from home_automation import downstream


logger = logging.getLogger(__name__)


SUPPORTED_VERSIONS = {1}


class JSONHandler(FileSystemEventHandler):

    def __init__(self, config: dict) -> None:
        self.config = config


    def on_created(self, event: FileCreatedEvent) -> None:
        self._handle(event.src_path)



    def on_modified(self, event: FileModifiedEvent) -> None:
        self._handle(event.src_path)


    def _handle(self, src_path: str) -> None:
        path = Path(src_path)
        if path.suffix.lower() != ".json":
            return
        if not path.name.startswith("proc_"):
            return
        logger.info("New JSON detected: %s", path)

        try:
            doc = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to read JSON %s: %s", path.name, e)
            return
        if doc.get("schema_version") not in SUPPORTED_VERSIONS:
            logger.warning("Unknown schema_version in %s: %s, attempting anyway", path.name, doc.get("schema_version"))
        downstream.process(doc, path.with_suffix(".pdf"), self.config)

        
def start(folders: list[str], config: dict) -> Observer:
    handler = JSONHandler(config)
    observer = Observer()
    for folder in folders:
        expanded = str(Path(folder).expanduser())
        try:
            observer.schedule(handler, expanded, recursive=True)
            logger.info("Watching for JSONs: %s", expanded)
        except FileNotFoundError:
            logger.warning("Folder not found, skipping: %s", expanded)

    observer.start()
    return observer
