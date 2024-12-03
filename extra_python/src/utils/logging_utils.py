import logging

def set_logging(log_name, level=logging.INFO):
    logger = logging.getLogger(log_name)
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(filename)s:%(lineno)d:%(message)s') )
    logger.addHandler(ch)
    return logger