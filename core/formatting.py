"""Format angka untuk tampilan lokal Indonesia."""

from decimal import Decimal, ROUND_HALF_UP


def format_rupiah(amount) -> str:
    """Format nilai rupiah tanpa pecahan dengan pemisah ribuan titik."""
    rounded = int(Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return f"Rp {rounded:,}".replace(",", ".")
