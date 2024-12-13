from threading import Lock


class ThreadSafeList:
    def __init__(self):
        self._list = []
        self._lock = Lock()

    def append(self, item):
        with self._lock:
            self._list.append(item)

    def sort(self, key=None):
        with self._lock:
            self._list.sort(key=key)

    def get_snapshot(self):
        """
        Returns a snapshot (copy) of the current list for safe iteration or inspection.
        """
        with self._lock:
            return list(self._list)
