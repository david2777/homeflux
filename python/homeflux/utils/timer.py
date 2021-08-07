import time


class Timer(object):
    """Simple Timer"""
    def __init__(self):
        self.start = time.perf_counter()

    def end(self, precision: int = 3) -> str:
        return '%.{}f'.format(precision) % (time.perf_counter() - self.start)
