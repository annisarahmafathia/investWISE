"""Fasilitas Penjelasan (Explanation Facility): Menyajikan penjelasan WHY dan HOW."""

from typing import Dict, Any
from core.inference_engine import INSTRUMENT_LABEL, ConsultationResult
from core.formatting import format_rupiah


def _then_text(rule: Dict[str, Any]) -> str:
    """Ubah bagian consequent (THEN) menjadi narasi yang mudah dipahami."""
    then = rule.get("then", {})
    if "fact" in then:
        return f"Tetapkan fakta {then['fact']} = '{then['value']}'"
    if "hypothesis" in then:
        return f"Mendukung profil risiko '{then['hypothesis']}'"
    if "adjust" in then:
        adj = ", ".join(f"{INSTRUMENT_LABEL.get(k, k)} {v:+d}%" for k, v in then["adjust"].items())
        return f"Sesuaikan proporsi alokasi: [{adj}]"
    return str(then)


def explain_why(kb, question_id: str) -> str:
    """Fasilitas WHY: Menjelaskan alasan mengapa sistem pakar menanyakan pertanyaan tertentu."""
    for q in kb.questions:
        if q["id"] == question_id:
            why_text = q.get("why", "Pertanyaan ini diperlukan untuk proses inferensi sistem pakar.")
            return f"💡 **Mengapa ditanyakan?**\n{why_text}"
    return "Pertanyaan ini merupakan parameter penentu dalam basis pengetahuan sistem pakar."


def explain_how(kb, result: ConsultationResult) -> str:
    """Fasilitas HOW: Menjelaskan langkah penalaran, rule yang teraktivasi, dan dasar kesimpulan sistem."""
    lines = [
        f"🎯 **Hasil Diagnosa Profil:** {result.profile.upper()}",
        f"⭐ **Tingkat Kepercayaan (Certainty Factor):** {result.confidence:.1%}",
        "",
        "📊 **Rekomendasi Alokasi Aset:**",
    ]

    for inst, pct in result.allocation.items():
        label = INSTRUMENT_LABEL.get(inst, inst)
        nominal_str = f" ({format_rupiah(result.nominal_allocation[inst])})" if result.nominal_allocation.get(inst) else ""
        lines.append(f"  • **{label}:** {pct}%{nominal_str}")

    lines.append("")
    lines.append("🔍 **Daftar Aturan Pakar yang Teraktivasi (Fired Rules):**")
    for i, rid in enumerate(result.fired_rules, 1):
        rule = kb.get_rule(rid)
        if not rule:
            continue
        cf_str = f" | [CF Pakar: {rule['cf']:.2f}]" if "cf" in rule else ""
        cond = " AND ".join(
            f"{c['fact']} {c['op']} '{c['value']}'" if isinstance(c['value'], str) else f"{c['fact']} {c['op']} {c['value']}"
            for c in rule["if"]
        )
        source = f" (Sumber: {rule.get('source', 'Pakar Keuangan')})"
        lines.append(f"  {i}. **[{rid}]** IF {cond} THEN {_then_text(rule)}{cf_str}{source}")

    lines.append("")
    lines.append("📋 **Alur Penalaran Rinci (Reasoning Trace):**")
    for i, (phase, text) in enumerate(result.trace, 1):
        lines.append(f"  {i}. `[{phase}]` {text}")

    if result.warnings:
        lines.append("")
        lines.append("⚠️ **Peringatan / Catatan Finansial:**")
        for w in result.warnings:
            lines.append(f"  • {w}")

    desc = kb.profile_info.get(result.profile, "")
    if desc:
        lines.append("")
        lines.append(f"ℹ️ **Karakteristik Profil:** {desc}")

    lines.append("")
    lines.append("⚖️ *Disclaimer: Rekomendasi ini adalah simulasi edukasi berbasis sistem pakar, bukan anjuran investasi mutlak.*")

    return "\n".join(lines)
