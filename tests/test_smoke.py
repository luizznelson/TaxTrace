import unittest

import taxtrace


class SmokeTest(unittest.TestCase):
    def test_package_has_version(self) -> None:
        self.assertEqual(taxtrace.__version__, "0.0.1")


if __name__ == "__main__":
    unittest.main()
