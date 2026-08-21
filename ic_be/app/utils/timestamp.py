from datetime import datetime, timezone


def get_now():
    now = datetime.now(timezone.utc)
    return now


def get_now_formatted(now=get_now()):
    return now.strftime("%Y-%m-%d %H:%M:%S.%f")
