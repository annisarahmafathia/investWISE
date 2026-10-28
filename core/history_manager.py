"""Pengelola Riwayat Konsultasi (History & Statistics): Menyimpan, mencari, memfilter riwayat dan statistik sistem."""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class HistoryManager:
    """Mengelola pencatatan riwayat sesi konsultasi dan analitik statistik sistem."""

    def __init__(self, filepath: str = "data/consultation_history.json"):
        self.filepath = filepath
        self.history: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        """Muat data riwayat dari file JSON."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []
        else:
            self.history = []

    def save(self) -> None:
        """Simpan riwayat ke file JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def add_entry(self, user_name: str, result, inputs: Dict[str, Any], modal: float = 0.0) -> Dict[str, Any]:
        """Catat satu sesi konsultasi ke riwayat."""
        entry = {
            "id": f"KONSUL-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.history)+1}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_name": user_name or "Investor Pemula",
            "profile": result.profile,
            "confidence": round(result.confidence, 4),
            "modal": modal,
            "allocation": result.allocation,
            "fired_rules": result.fired_rules,
            "inputs": inputs,
            "warnings": result.warnings,
        }
        self.history.insert(0, entry)  # Terbaru di posisi awal
        self.save()
        return entry

    def filter_history(self, profile: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter riwayat berdasarkan profil dan kata kunci pencarian."""
        results = self.history
        if profile and profile.lower() != "semua":
            results = [e for e in results if e.get("profile", "").lower() == profile.lower()]
        if search_query:
            q = search_query.lower()
            results = [
                e for e in results
                if q in e.get("user_name", "").lower() or
                   q in e.get("id", "").lower() or
                   q in e.get("profile", "").lower() or
                   q in e.get("timestamp", "").lower()
            ]
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Hitung statistik penggunaan sistem pakar dan frekuensi penggunaan rule."""
        total_sessions = len(self.history)
        if total_sessions == 0:
            return {
                "total_sessions": 0,
                "profile_counts": {"konservatif": 0, "moderat": 0, "agresif": 0},
                "avg_confidence": 0.0,
                "rule_frequency": {},
                "avg_modal": 0.0,
            }

        profile_counts = {"konservatif": 0, "moderat": 0, "agresif": 0}
        total_conf = 0.0
        rule_freq = {}
        total_modal = 0.0

        for e in self.history:
            prof = e.get("profile", "moderat")
            profile_counts[prof] = profile_counts.get(prof, 0) + 1
            total_conf += e.get("confidence", 0.0)
            total_modal += e.get("modal", 0.0)

            for rid in e.get("fired_rules", []):
                rule_freq[rid] = rule_freq.get(rid, 0) + 1

        # Urutkan frekuensi rule terbanyak
        sorted_rules = dict(sorted(rule_freq.items(), key=lambda item: item[1], reverse=True))

        return {
            "total_sessions": total_sessions,
            "profile_counts": profile_counts,
            "avg_confidence": round(total_conf / total_sessions, 4),
            "rule_frequency": sorted_rules,
            "avg_modal": round(total_modal / total_sessions, 2),
        }
