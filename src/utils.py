def get_is_queue(obj):
    return hasattr(obj, "put") and callable(getattr(obj, "put"))
