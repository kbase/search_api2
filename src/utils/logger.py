import os
import sys
import logging


def init_logger():
    """
    Initialize log settings. Mutates the `logger` object.
    """
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logger = logging.getLogger('search2')
    # Set the log level
    level = os.environ.get('LOGLEVEL', 'DEBUG').upper()
    logger.setLevel(level)
    logger.propagate = False  # Don't print duplicate messages
    logging.basicConfig(level=level)
    # Create the formatter
    fmt = "%(asctime)s %(levelname)-8s %(message)s (%(filename)s:%(lineno)s)"
    time_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, time_fmt)
    # Stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    print(f'Logger and level: {logger}')
    print(f'''
** To see more or less logging information, adjust the
** log level by setting the LOGLEVEL environment variable
** to one of:
**   CRITICAL ERROR WARNING INFO DEBUG NOTSET
** It is currently set to:
**   {level}
''')
    return logger


logger = init_logger()
