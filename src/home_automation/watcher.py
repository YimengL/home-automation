import json
import logging
import signal
from pathlib import Path
import threading

import pipeline
from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers.polling import PollingObserver
from home_automation import downstream


logger = logging.getLogger(__name__)

SUPPORTED_VERSIONS = {1}


class FolderHandler(FileSystemEventHandler):

    _sem = threading.Semaphore(1)  # serialize PDF translations to avoid OOM

    def __init__(self, config: dict) -> None:
        self.config = config
        self.watch_root = Path(config["watch_folder"]).expanduser().resolve()


    def _handle(self, str_path: str) -> None:
        path = Path(str_path)

        # Route based on filename pattern
        if path.suffix.lower() != ".json":
            return
        if not path.name.startswith("proc_"):
            return
        logger.info("New JSON file detected: %s", path)
        threading.Thread(target=self._process, args=(path,), daemon=True).start()

    
    def _process(self, path: Path) -> None:
        try:
            doc = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to read JSON %s: %s", path.name, e)
            return
        if doc.get("schema_version") not in SUPPORTED_VERSIONS:
            logger.warning("Unknown schema_version in %s, attempting anyway", path.name)
        downstream.process(doc, path.with_suffix(".pdf"), self.config)


    def _handle_pdf(self, str_path: str) -> None:
        path = Path(str_path)
        if path.suffix.lower() != ".pdf" or not path.name.startswith("ori_"):
            return
        logger.info("New PDF detected: %s", path)
        threading.Thread(target=self._process_pdf, args=(path,), daemon=True).start()

    def _process_pdf(self, path: Path) -> None:
        with FolderHandler._sem:
            output_path = pipeline.derive_output_path(path)
            pipeline.main(str(path), str(output_path))


    def on_created(self, event: FileCreatedEvent) -> None:
        self._handle(event.src_path)
        self._handle_pdf(event.src_path)
    

    def on_modified(self, event) -> None:
        self._handle_pdf(event.src_path)

    
    def on_moved(self, event: FileMovedEvent) -> None:
        self._handle(event.dest_path)
        src = Path(event.src_path).resolve()
        dest = Path(event.dest_path)
        renamed_to_ori = dest.name.startswith("ori_") and not src.name.startswith("ori_")
        same_parent = src.parent.resolve() == dest.parent.resolve()
        moved_in = not src.is_relative_to(self.watch_root)
        if (renamed_to_ori and same_parent) or moved_in:
            self._handle_pdf(event.dest_path)
        else:
            logger.debug("Ignored move: %s → %s (internal reorganization)", src.name, dest.name)


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