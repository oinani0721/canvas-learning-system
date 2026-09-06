class C:
    def m(self):
        with self._lock:
            pass
