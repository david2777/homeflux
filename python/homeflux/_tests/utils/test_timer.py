"""Tests for homeflux.utils.timer"""
import time
import unittest

from homeflux.utils.timer import Timer


class TestTimer(unittest.TestCase):
    def test_timer(self):
        t = Timer()
        time.sleep(0.1)
        self.assertEqual('0.1', t.end(precision=1))


if __name__ == '__main__':
    unittest.main()
