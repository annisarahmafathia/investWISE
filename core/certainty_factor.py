"""Modul perhitungan Certainty Factor (CF) untuk sistem pakar alokasi aset.

Mendukung:
- Perhitungan serial: CF(H, E) = CF(E) * CF(Rule)
- Konjungsi AND: CF(E1 AND E2) = min(CF(E1), CF(E2))
- Disjungsi OR: CF(E1 OR E2) = max(CF(E1), CF(E2))
- Kombinasi paralel (multiple evidence) untuk rentang [-1.0 s.d +1.0] dan [0.0 s.d 1.0]
"""

from typing import List


def cf_rule(cf_user: float, cf_pakar: float) -> float:
    """Hitung CF satu rule teraktivasi: CF(H, E) = CF(user) x CF(pakar)."""
    return round(cf_user * cf_pakar, 4)


def cf_combine(cf1: float, cf2: float) -> float:
    """Gabungkan dua nilai CF (Shortliffe & Buchanan).

    - Jika keduanya positif: CF1 + CF2 * (1 - CF1)
    - Jika keduanya negatif: CF1 + CF2 * (1 + CF1)
    - Jika berlawanan tanda: (CF1 + CF2) / (1 - min(|CF1|, |CF2|))
    """
    if cf1 >= 0 and cf2 >= 0:
        return cf1 + cf2 * (1.0 - cf1)
    elif cf1 < 0 and cf2 < 0:
        return cf1 + cf2 * (1.0 + cf1)
    else:
        denom = 1.0 - min(abs(cf1), abs(cf2))
        if denom == 0:
            return 0.0
        return (cf1 + cf2) / denom


def cf_combine_all(cfs: List[float]) -> float:
    """Gabungkan daftar nilai CF secara kumulatif."""
    if not cfs:
        return 0.0
    result = cfs[0]
    for cf in cfs[1:]:
        result = cf_combine(result, cf)
    return round(result, 4)


def cf_and(cfs: List[float]) -> float:
    """Konjungsi AND untuk antecedent majemuk: min(CF)."""
    return min(cfs) if cfs else 1.0


def cf_or(cfs: List[float]) -> float:
    """Disjungsi OR untuk antecedent majemuk: max(CF)."""
    return max(cfs) if cfs else 0.0
