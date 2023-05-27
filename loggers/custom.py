import logging
import logging.config
from datetime import datetime


def logging_custom(__name__):
    logging.config.fileConfig(
        'loggers/logging.conf',
        defaults={'logfilename': 'loggers/logs/{:%Y-%m-%d}.log'.format(datetime.now())},
    )
    logger = logging.getLogger(__name__)
    return logger


class AppLogger:
    _logger_file = 'loggers/logs/{:%Y-%m-%d}.log'.format(datetime.now())
    _LOGGER_CONFIG = 'loggers/logging.conf'

    def get_logger(self):
        self._logger = logging.getLogger(__name__)
        logging.config.fileConfig(
            self._LOGGER_CONFIG,
            defaults={'logfilename': self._logger_file}
        )
        return self._logger
