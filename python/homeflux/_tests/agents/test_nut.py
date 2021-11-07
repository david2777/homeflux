import unittest

from homeflux.agents import nut


class TestNut(unittest.TestCase):
    def test_init(self):
        ins = nut.NutClient('localhost', '127.0.0.1', 'hour')
        self.assertIsInstance(ins, nut.NutClient)

    def test_bad_timescale_init(self):
        with self.assertRaises(ValueError):
            nut.NutClient('localhost', '127.0.0.1', 'year')


if __name__ == '__main__':
    unittest.main()
