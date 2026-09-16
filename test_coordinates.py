import unittest

from coordinates import normalize_coordinates


class NormalizeCoordinatesTest(unittest.TestCase):
    def test_normalizes_vietnamese_decimal_commas(self) -> None:
        self.assertEqual(
            normalize_coordinates("10,90242° B, 106,59664° Đ"),
            "10.90242, 106.59664",
        )

    def test_applies_south_and_west_as_negative(self) -> None:
        self.assertEqual(
            normalize_coordinates("10,5° N; 106,25° T"),
            "-10.5, -106.25",
        )

    def test_rejects_coordinates_outside_valid_range(self) -> None:
        with self.assertRaises(ValueError):
            normalize_coordinates("91° B, 106° Đ")

    def test_rejects_unrecognized_text(self) -> None:
        with self.assertRaises(ValueError):
            normalize_coordinates("xin chào")


if __name__ == "__main__":
    unittest.main()
