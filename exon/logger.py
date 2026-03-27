# Create a custom formatter to have nice colors when displaying logging messages
# See https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
import logging

# ANSI color codes
# For standard colors:
#  - Font colors: \x1b[30m to \x1b[37m for text (black to white).
#  - Background colors: \x1b[40m to \x1b[47m for background.
# For fancy colors:
#  - Font colors: \x1b[38;5;<color_code>m
#  - Background colors: \x1b[48;5;<color_code>m
# -> For colors codes, See https://github.com/fidian/ansi

RESET = "\x1b[0m"
GREY = "\x1b[0;30m"
YELLOW = "\x1b[0;33m"
BRIGHT_RED = "\x1b[38;5;196m"
BOLD_RED = "\x1b[1;31m"
BLUE = "\x1b[38;5;86m"


class ExonFormatter(logging.Formatter):

    message_format = "%(asctime)s - %(levelname)s - %(message)s"
    FORMATS = {
        logging.DEBUG: GREY + message_format + RESET,
        logging.INFO: BLUE + message_format + RESET,
        logging.WARNING: YELLOW + message_format + RESET,
        logging.ERROR: BOLD_RED + message_format + RESET,
        logging.CRITICAL: BRIGHT_RED + message_format + RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def configure_logger() -> None:
    # TO DO -> Implement verbosity
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(ExonFormatter())
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
