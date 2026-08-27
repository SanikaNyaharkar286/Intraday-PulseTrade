import logging


def get_logger(name: str):

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(threadName)s | "
            "%(message)s"
        )
    )

    return logging.getLogger(name)