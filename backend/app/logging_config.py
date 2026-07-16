import logging
import sys

from app.config import settings


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


def configure_logging() -> None:
    """
    Configure application-wide logging.
    """

    log_level = getattr(
        logging,
        settings.log_level,
        logging.INFO,
    )

    root_logger = logging.getLogger()

    if root_logger.handlers:
        root_logger.setLevel(
            log_level
        )

        for handler in (
            root_logger.handlers
        ):
            handler.setLevel(
                log_level
            )

        return

    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(
                sys.stdout
            )
        ],
        force=True,
    )