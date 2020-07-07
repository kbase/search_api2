
def get_path(obj, path):
    """Fetch data from an object with nested, or return None. Avoids raising."""
    for each in path:
        try:
            obj = obj[each]
        except Exception:
            return None
    return obj


def get_any(obj, keys, default=None):
    """
    Return the first non-None value from any key in `keys`, in order
    If all are None, then returns `default`
    """
    for key in keys:
        val = obj.get(key)
        if val is not None:
            return val
    return default
