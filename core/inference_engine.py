"""Inference engine: forward chaining dengan Certainty Factor dan trace penalaran step-by-step."""

from dataclasses import dataclass, field
from decimal import Decimal
import math
from typing import Dict, List, Any, Optional, Tuple

from core.certainty_factor import cf_rule, cf_combine_all, cf_and
from core.allocations import allocate_nominal
from core.working_memory import WorkingMemory

PROFILE_ORDER = ("konservatif", "moderat", "agresif")  # urutan tie-break konservatif bila skor sama
INSTRUMENT_LABEL = {
    "reksa_dana": "Reksa Dana (Pasar Uang & Pendapatan Tetap)",
    "obligasi": "Obligasi / SBN (Surat Berharga Negara)",
    "emas": "Emas Logam Mulia",
    "saham": "Saham (Indeks LQ45 / Bluechip)",
}


@dataclass
class ConsultationResult:
    """Hasil akhir komprehensif dari satu sesi konsultasi sistem pakar."""
    profile: str
    confidence: float
    scores: Dict[str, float]
    allocation: Dict[str, int]
    nominal_allocation: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    fired_rules: List[str] = field(default_factory=list)
    trace: List[Tuple[str, str]] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)
    user_inputs: Dict[str, Any] = field(default_factory=dict)
    user_cf: Dict[str, float] = field(default_factory=dict)


class InferenceEngine:
    """Mesin inferensi Forward Chaining (Data-Driven) berbasis Certainty Factor."""

    def __init__(self, kb):
        self.kb = kb

    def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validasi data masukan pengguna sesuai batasan questions di Knowledge Base."""
        for q in self.kb.questions:
            qid = q["id"]
            if qid not in inputs:
                raise ValueError(f"Pertanyaan '{q.get('label', qid)}' wajib diisi.")
            val = inputs[qid]
            if q["type"] == "number":
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise ValueError(f"'{q.get('label', qid)}' harus berupa angka.")
                if not math.isfinite(float(val)):
                    raise ValueError(f"'{q.get('label', qid)}' harus berupa angka yang valid.")
                if "min" in q and val < q["min"]:
                    raise ValueError(f"'{q.get('label', qid)}' tidak boleh kurang dari {q['min']}.")
                if "max" in q and val > q["max"]:
                    raise ValueError(f"'{q.get('label', qid)}' tidak boleh lebih dari {q['max']}.")
            elif q["type"] == "choice":
                if val not in q["options"]:
                    raise ValueError(f"Pilihan '{val}' tidak valid untuk '{q.get('label', qid)}'.")

    @staticmethod
    def _compare(actual: Any, op: str, expected: Any) -> bool:
        """Evaluasi operator relasional matematika/string."""
        try:
            if op == "==":
                return actual == expected
            elif op == "!=":
                return actual != expected
            elif op == "<":
                return actual < expected
            elif op == "<=":
                return actual <= expected
            elif op == ">":
                return actual > expected
            elif op == ">=":
                return actual >= expected
            return False
        except TypeError:
            return False

    def _match(self, rule: Dict[str, Any], wm: WorkingMemory) -> Tuple[bool, float]:
        """Periksa kesesuaian antecedent (IF) rule terhadap fakta di Working Memory.

        Return:
            (is_matched, cf_antecedent)
        """
        cfs = []
        for cond in rule["if"]:
            fact = wm.get(cond["fact"])
            if fact is None:
                return False, 0.0
            if not self._compare(fact.value, cond["op"], cond["value"]):
                return False, 0.0
            cfs.append(fact.cf)
        return True, cf_and(cfs)

    @staticmethod
    def _cond_text(rule: Dict[str, Any]) -> str:
        """Format kondisi IF menjadi string yang mudah dibaca."""
        return " AND ".join(f"{c['fact']} {c['op']} '{c['value']}'" if isinstance(c['value'], str) else f"{c['fact']} {c['op']} {c['value']}" for c in rule["if"])

    def _forward_chain(self, wm: WorkingMemory) -> None:
        """Siklus Forward Chaining: Ekstraksi fakta turunan (derive) dan pengumpulan evidence profil."""
        changed = True
        cycle = 1
        while changed:
            changed = False
            for rule in self.kb.rules_of_type("derive", "profile"):
                if wm.has_fired(rule["id"]):
                    continue
                matched, cf_user = self._match(rule, wm)
                if not matched:
                    continue

                wm.mark_fired(rule["id"])
                changed = True

                if rule["type"] == "derive":
                    fact_name = rule["then"]["fact"]
                    fact_val = rule["then"]["value"]
                    wm.add_fact(fact_name, fact_val, cf=cf_user, origin=rule["id"])
                    wm.log(
                        "DERIVASI FAKTA",
                        f"Rule {rule['id']} aktif: IF {self._cond_text(rule)} "
                        f"THEN {fact_name} = '{fact_val}' (Sumber: {rule.get('source', 'Pakar')})"
                    )
                elif rule["type"] == "profile":
                    hyp = rule["then"]["hypothesis"]
                    rule_cf = rule.get("cf", 1.0)
                    cf_combined = cf_rule(cf_user, rule_cf)
                    wm.add_evidence(hyp, rule["id"], cf_combined)
                    wm.log(
                        "EVIDENCE PROFIL",
                        f"Rule {rule['id']} aktif: IF {self._cond_text(rule)} "
                        f"THEN profil risiko '{hyp}' | CF_User({cf_user:.2f}) x CF_Pakar({rule_cf:.2f}) = {cf_combined:.2f}"
                    )
            cycle += 1

    def _conclude_profile(self, wm: WorkingMemory) -> Tuple[str, Dict[str, float]]:
        """Hitung Certainty Factor gabungan untuk setiap profil dan tentukan kesimpulan final."""
        scores = {}
        for h in PROFILE_ORDER:
            evidence_cfs = [e.cf for e in wm.evidences.get(h, [])]
            scores[h] = cf_combine_all(evidence_cfs) if evidence_cfs else 0.0

        # Menentukan profil dengan nilai CF tertinggi (prioritas konservatif pada skor sama)
        best_profile = PROFILE_ORDER[0]
        max_score = scores[best_profile]
        for h in PROFILE_ORDER:
            if scores[h] > max_score:
                max_score = scores[h]
                best_profile = h

        wm.add_fact("profil_final", best_profile, cf=scores[best_profile], origin="CF-Inference")
        ringkasan = ", ".join(f"{h.capitalize()}: {scores[h]:.1%}" for h in PROFILE_ORDER)
        wm.log(
            "KESIMPULAN PROFIL",
            f"Kombinasi CF: [{ringkasan}] => Profil Terpilih: {best_profile.upper()} "
            f"dengan tingkat kepastian {scores[best_profile]:.1%}"
        )
        return best_profile, scores

    def _allocate(self, wm: WorkingMemory, profile: str, modal_investasi: float = 0.0) -> Tuple[Dict[str, int], Dict[str, float], List[str]]:
        """Hitung rekomendasi alokasi aset berbasis template dasar dan rule penyesuaian (adjust)."""
        alloc = dict(self.kb.templates.get(profile, {"reksa_dana": 30, "obligasi": 30, "emas": 20, "saham": 20}))
        wm.log(
            "TEMPLATE DASAR",
            f"Template alokasi dasar profil '{profile}': " +
            ", ".join(f"{k}: {v}%" for k, v in alloc.items())
        )

        warnings = []
        for rule in self.kb.rules_of_type("adjust"):
            matched, _ = self._match(rule, wm)
            if not matched:
                continue

            wm.mark_fired(rule["id"])
            adjustments = rule["then"].get("adjust", {})
            for inst, delta in adjustments.items():
                alloc[inst] = alloc.get(inst, 0) + delta

            adj_text = ", ".join(f"{k} {v:+d}%" for k, v in adjustments.items())
            wm.log(
                "ADJUSTMENT ALOKASI",
                f"Rule {rule['id']} aktif: IF {self._cond_text(rule)} THEN penyesuaian [{adj_text}]"
            )
            if rule.get("warning"):
                warnings.append(rule["warning"])

        # Normalisasi dan terapkan batas bawah
        alloc = self._normalize(alloc)
        alloc = self._apply_floor(alloc, wm)

        nominal = allocate_nominal(alloc, modal_investasi)

        wm.log(
            "HASIL AKHIR ALOKASI",
            "Alokasi final (terverifikasi 100%): " + ", ".join(f"{k}: {v}%" for k, v in alloc.items())
        )
        return alloc, nominal, warnings

    def _apply_floor(self, alloc: Dict[str, int], wm: WorkingMemory) -> Dict[str, int]:
        """Pastikan instrumen likuid (misal reksa dana pasar uang) tidak 0% sebagai pengaman."""
        for inst, floor in self.kb.min_allocation.items():
            if alloc.get(inst, 0) < floor:
                diff = floor - alloc.get(inst, 0)
                # Ambil selisih dari instrumen dengan porsi terbesar (selain instrumen bersangkutan)
                candidates = [k for k in alloc.keys() if k != inst]
                donor = max(candidates, key=lambda k: alloc[k])
                alloc[inst] += diff
                alloc[donor] -= diff
                wm.log("PROTEKSI LIKUIDITAS", f"Batas aman minimal {inst} {floor}% terpenuhi dengan menggeser {diff}% dari {donor}")
        return alloc

    @staticmethod
    def _normalize(alloc: Dict[str, int]) -> Dict[str, int]:
        """Normalisasi persentase ke total tepat 100% menggunakan metode sisa terbesar (Largest Remainder)."""
        clamped = {k: max(v, 0) for k, v in alloc.items()}
        total = sum(clamped.values())
        if total <= 0:
            raise ValueError("Total alokasi aset harus lebih dari 0%.")
        raw = {k: (v * 100.0) / total for k, v in clamped.items()}
        result = {k: int(v) for k, v in raw.items()}
        leftover = 100 - sum(result.values())
        for k in sorted(raw.keys(), key=lambda x: raw[x] - result[x], reverse=True)[:leftover]:
            result[k] += 1
        return result

    def run(self, inputs: Dict[str, Any], user_cf: Optional[Dict[str, float]] = None, modal_investasi: float = 0.0) -> ConsultationResult:
        """Jalankan siklus konsultasi inferensi forward chaining."""
        self.validate_inputs(inputs)
        if isinstance(modal_investasi, bool) or not isinstance(modal_investasi, (int, float)):
            raise ValueError("Modal investasi harus berupa angka rupiah.")
        if not math.isfinite(float(modal_investasi)) or modal_investasi < 0:
            raise ValueError("Modal investasi harus berupa angka rupiah yang tidak negatif.")
        modal_decimal = Decimal(str(modal_investasi))
        if not modal_decimal.is_finite() or modal_decimal != modal_decimal.to_integral_value():
            raise ValueError("Modal investasi harus berupa angka rupiah bulat yang valid.")
        user_cf = user_cf or {}
        wm = WorkingMemory()

        for name, value in inputs.items():
            cf = user_cf.get(name, 1.0)
            if not (0 < cf <= 1.0):
                raise ValueError(f"Certainty Factor pengguna untuk '{name}' harus berada dalam rentang 0 < CF <= 1.0")
            wm.add_fact(name, value, cf=cf, origin="input_pengguna")

        input_summary = ", ".join(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in inputs.items())
        wm.log("INISIALISASI", f"Fakta awal pengguna diterima: [{input_summary}]")

        self._forward_chain(wm)
        profile, scores = self._conclude_profile(wm)
        allocation, nominal, warnings = self._allocate(wm, profile, modal_investasi)

        return ConsultationResult(
            profile=profile,
            confidence=scores[profile],
            scores=scores,
            allocation=allocation,
            nominal_allocation=nominal,
            warnings=warnings,
            fired_rules=list(wm.fired),
            trace=list(wm.trace),
            facts={n: f.value for n, f in wm.facts.items()},
            user_inputs=dict(inputs),
            user_cf=dict(user_cf),
        )
