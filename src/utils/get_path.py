

def get_path(obj, path):
    """Fetch data from an object with nested, or return None. Avoids raising."""
    for each in path:
        try:
            obj = obj[each]
        except Exception:
            return None
    return obj
