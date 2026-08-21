import logging
import os
import datetime
import zoneinfo

_VN_TZ = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")


class _VNFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.datetime.fromtimestamp(record.created, tz=_VN_TZ)
        return dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S")


_FORMATTER = _VNFormatter(
    "[%(asctime)s] [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str = "inventory", log_file: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(_FORMATTER)
    logger.addHandler(ch)

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(_FORMATTER)
        logger.addHandler(fh)

    logger.propagate = False
    return logger
