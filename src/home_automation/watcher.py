import json
import logging
import signal
import time
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
        done_path = path.with_name("done_" + path.name[len("proc_"):])
        path.rename(done_path)
        logger.info("Renamed %s -> %s", path.name, done_path.name)


    def _handle_pdf(self, str_path: str) -> None:
        path = Path(str_path)
        if path.suffix.lower() != ".pdf" or not path.name.startswith("ori_"):
            return
        proc_pdf = path.with_name("proc_" + path.name[len("ori_"):])
        if proc_pdf.exists():
            logger.info("Skipping %s - %s already exists", path.name, proc_pdf.name)
            return
        logger.info("New PDF detected: %s", path)
        threading.Thread(target=self._process_pdf, args=(path,), daemon=True).start()

    def _process_pdf(self, path: Path) -> None:
        time.sleep(self.config.get("translate_debounce_s", 10))
        proc_pdf = path.with_name("proc_" + path.name[len("ori_"):])
        if proc_pdf.exists():
            logger.info("Skipping %s after debounce - %s appeared", path.name, proc_pdf.name)
            return
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
        self._handle_pdf(event.dest_path)


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