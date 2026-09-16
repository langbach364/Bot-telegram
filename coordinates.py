import re
import unicodedata
from decimal import Decimal


COORDINATE_PATTERN = re.compile(
    r"^\s*(\d+(?:[.,]\d+)?)\s*°?\s*([BN])\s*[,;]?\s*"
    r"(\d+(?:[.,]\d+)?)\s*°?\s*([ĐDT])\s*$",
    re.IGNORECASE,
)


def _direction(value: str) -> str:
    return unicodedata.normalize("NFC", value).upper()


def _decimal(value: str) -> Decimal:
    return Decimal(value.replace(",", "."))


def normalize_coordinates(text: str) -> str:
    """Convert Vietnamese latitude/longitude notation to decimal degrees."""
    match = COORDINATE_PATTERN.fullmatch(unicodedata.normalize("NFC", text))
    if not match:
        raise ValueError("Định dạng tọa độ không hợp lệ")

    latitude = _decimal(match.group(1))
    longitude = _decimal(match.group(3))

    if latitude > 90 or longitude > 180:
        raise ValueError("Tọa độ nằm ngoài phạm vi hợp lệ")

    if _direction(match.group(2)) == "N":  # Nam (South)
        latitude = -latitude
    if _direction(match.group(4)) == "T":  # Tây (West)
        longitude = -longitude

    return f"{latitude:f}, {longitude:f}"
