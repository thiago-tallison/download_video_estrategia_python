import re

MAX_FILENAME_LENGTH = 200


def sanitize_filename(name):
    name = re.sub(r'[\/:*?"<>|]', "_", name)
    return name


def truncate_filename(filename, max_length=MAX_FILENAME_LENGTH):
    if len(filename) <= max_length:
        return filename
    else:
        return filename[: max_length - 3] + "..."
