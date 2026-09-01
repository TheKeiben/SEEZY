import logging
from PyQt6.QtCore import QObject, pyqtSignal

class QtLogHandler(logging.Handler, QObject):
    """Custom logging handler to emit log records as Qt signals."""
    log_signal = pyqtSignal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

def setup_logger():
    """Configures the root logger and attaches the Qt signal handler."""
    logger = logging.getLogger("SEEZY")
    logger.setLevel(logging.INFO)
    
    # Console output handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(console_handler)

    # Qt Signal Handler
    qt_handler = QtLogHandler()
    logger.addHandler(qt_handler)

    return logger, qt_handler