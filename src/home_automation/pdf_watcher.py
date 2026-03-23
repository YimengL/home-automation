import logging
import subprocess
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers import Observer


logger = logging.getLogger(__name__)


class PDFHandler(FileSystemEventHandler):


    def __init__(self, translate_bin: str) -> None:
        self.translate_bin = translate_bin


    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".pdf":
            return
        if not path.name.startswith("ori_"):
            return
        logger.info("New PDF detected: %s", path)
        self._run_translate(path)
    

    def on_moved(self, event: FileMovedEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.dest_path)
        if path.suffix.lower() != ".pdf":
            return
        if not path.name.startswith("ori_"):
            return
        logger.info("PDF renamed to ori_: %s", path)
        self._run_translate(path)

    
    def _run_translate(self, path: Path) -> None:
        try:
            subprocess.run([self.translate_bin, str(path)], check=True)
            logger.info("Translate completed: %s", path.name)
        except subprocess.CalledProcessError as e:
            logger.error("Translate fail for %s: %s", path.name, e)


def start(folders: list[str], translate_bin: str) -> Observer:
    handler = PDFHandler(translate_bin)
    observer = Observer()
    for folder in folders:
        expanded = str(Path(folder).expanduser())
        try:
            observer.schedule(handler, expanded, recursive=True)
            logger.info("Watching for PDFs: %s", expanded)
        except FileNotFoundError:
            logger.warning("Folder not found, skipping: %s", expanded)
    
    observer.start()
    return observer