import unittest
from unittest.mock import patch


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)

    def test_incorrect_ocr(self):
        pass


if __name__ == '__main__':
    unittest.main()
