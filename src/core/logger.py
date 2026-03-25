import logging

_LOG_NAME = "ksh"
_configured = False


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """Configure the root ksh logger. Safe to call multiple times — only the first call takes effect."""
    global _configured
    logger = logging.getLogger(_LOG_NAME)

    if not _configured:
        logger.setLevel(level)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        _configured = True

    return logger


def get_logger() -> logging.Logger:
    """Return the ksh logger without reconfiguring it."""
    return logging.getLogger(_LOG_NAME)
