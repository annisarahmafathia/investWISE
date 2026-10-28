"""Pembagian alokasi aset ke nominal rupiah utuh."""

from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from typing import Dict


def allocate_nominal(alloc: Dict[str, int], modal_investasi: float) -> Dict[str, int]:
    """Bagikan modal ke rupiah utuh dan pastikan jumlahnya tepat sama dengan modal."""
    modal = Decimal(str(modal_investasi))
    if modal <= 0:
        return {}

    total_rupiah = int(modal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    nominal_exact = {
        inst: Decimal(total_rupiah) * Decimal(str(pct)) / Decimal("100")
        for inst, pct in alloc.items()
    }
    nominal = {
        inst: int(value.to_integral_value(rounding=ROUND_FLOOR))
        for inst, value in nominal_exact.items()
    }
    sisa_rupiah = total_rupiah - sum(nominal.values())
    urutan_sisa = sorted(
        alloc,
        key=lambda inst: nominal_exact[inst] - nominal[inst],
        reverse=True,
    )
    for inst in urutan_sisa[:sisa_rupiah]:
        nominal[inst] += 1
    return nominal
