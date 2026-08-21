from regex import regex


def validate_fullname(fullname):
    return regex.match(r"^[\p{L}\s]+$", fullname)