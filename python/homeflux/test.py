"""Test Point of Entry"""
import unittest


def main():
    loader = unittest.TestLoader()
    tests = loader.discover('_tests')
    test_runner = unittest.runner.TextTestRunner()
    test_runner.run(tests)


if __name__ == '__main__':
    main()
