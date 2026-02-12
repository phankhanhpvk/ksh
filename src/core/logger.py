import logging

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    return logging.getLogger("ksh_sync")
