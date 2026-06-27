import logging
import sys
from pathlib import Path

_log_dir_created = False

def _ensure_log_dir():
    global _log_dir_created
    log_dir = Path(__file__).parent.resolve() / "logs"
    if not _log_dir_created:
        log_dir.mkdir(exist_ok=True)
        _log_dir_created = True
    return log_dir

def setup_logger(name: str = "AKATSUKI") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        log_dir = _ensure_log_dir()
        fh = logging.FileHandler(log_dir / "akatsuki_app.log", encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s'))
        logger.addHandler(console)
        logger.addHandler(fh)
    return logger

logger = setup_logger()
