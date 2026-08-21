import re

def username_slug(username: str) -> str:
    """
    Xoá các chữ số ở cuối username (nếu có).
    Ví dụ:
      hoang_lf001 -> hoang_lf
      hoang02_lf21 -> hoang02_lf
      len_lf -> len_lf
    """
    return re.sub(r'\d+$', '', username)