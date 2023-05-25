import logging
import logging.config
from datetime import datetime


def logging_custom():
    logging.config.fileConfig(
        'loggers/logging.conf',
        defaults={'logfilename': 'loggers/logs/{:%Y-%m-%d}.log'.format(datetime.now())},
    )
    logger = logging.getLogger(__name__)
    return logger
