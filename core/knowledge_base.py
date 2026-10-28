"""Knowledge base: memuat, memvalidasi, menyimpan, dan memodifikasi rules dari file JSON."""

import json
import os
from typing import Dict, List, Optional, Any

VALID_TYPES = ("derive", "profile", "adjust")
VALID_OPS = ("==", "!=", "<", "<=", ">", ">=")
INSTRUMENTS = ("reksa_dana", "obligasi", "emas", "saham")


class KnowledgeBase:
    """Mengelola basis pengetahuan (rules, template alokasi dasar, pertanyaan, profil)."""

    def __init__(self, path: str):
        self.path = path
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Baca knowledge base dari file JSON."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"File knowledge base tidak ditemukan: {self.path}")
        try:
            with open(self.path, encoding="utf-8") as f:
                self.data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Format JSON knowledge base rusak: {e}")

    def save(self) -> None:
        """Simpan knowledge base ke file JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.data.get("metadata", {})

    @property
    def rules(self) -> List[Dict[str, Any]]:
        return self.data.get("rules", [])

    @property
    def templates(self) -> Dict[str, Dict[str, int]]:
        return self.data.get("templates", {})

    @property
    def min_allocation(self) -> Dict[str, int]:
        return self.data.get("min_allocation", {})

    @property
    def questions(self) -> List[Dict[str, Any]]:
        return self.data.get("questions", [])

    @property
    def profile_info(self) -> Dict[str, str]:
        return self.data.get("profile_info", {})

    def rules_of_type(self, *types: str) -> List[Dict[str, Any]]:
        """Ambil rule berdasarkan tipe (derive, profile, adjust)."""
        return [r for r in self.rules if r.get("type") in types]

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Ambil satu rule berdasarkan ID, atau None jika tidak ditemukan."""
        return next((r for r in self.rules if r["id"] == rule_id), None)

    def search_rules(self, query: str) -> List[Dict[str, Any]]:
        """Cari rule berdasarkan ID, deskripsi, atau kondisi."""
        q = query.lower()
        results = []
        for r in self.rules:
            text = f"{r.get('id', '')} {r.get('description', '')} {r.get('source', '')} {r.get('type', '')} {json.dumps(r.get('if', []))} {json.dumps(r.get('then', {}))}".lower()
            if q in text:
                results.append(r)
        return results

    def validate_rule(self, rule: Dict[str, Any], is_new: bool = False) -> None:
        """Validasi struktur rule sesuai skema sistem pakar."""
        for key in ("id", "type", "if", "then", "source"):
            if key not in rule or not rule[key]:
                raise ValueError(f"Field '{key}' wajib diisi pada rule")

        rule_type = rule["type"]
        if rule_type not in VALID_TYPES:
            raise ValueError(f"Tipe rule harus salah satu dari {VALID_TYPES}, ditemukan: '{rule_type}'")

        if is_new and self.get_rule(rule["id"]):
            raise ValueError(f"ID rule '{rule['id']}' sudah ada di database")

        if not isinstance(rule["if"], list) or len(rule["if"]) == 0:
            raise ValueError("Kondisi IF harus berupa daftar kondisi minimal 1")

        for cond in rule["if"]:
            if not isinstance(cond, dict):
                raise ValueError(f"Format kondisi harus objek dict: {cond}")
            if "fact" not in cond or "op" not in cond or "value" not in cond:
                raise ValueError(f"Kondisi harus memiliki 'fact', 'op', dan 'value': {cond}")
            if cond["op"] not in VALID_OPS:
                raise ValueError(f"Operator '{cond['op']}' tidak valid. Harus salah satu dari {VALID_OPS}")

        if rule_type == "profile":
            cf = rule.get("cf")
            if cf is None or not (0 < cf <= 1.0):
                raise ValueError("Rule bertipe 'profile' wajib memiliki nilai Certainty Factor di rentang 0 < CF <= 1.0")
            if "hypothesis" not in rule.get("then", {}):
                raise ValueError("Bagian THEN pada rule profile harus menentukan 'hypothesis' (konservatif/moderat/agresif)")

        elif rule_type == "derive":
            then = rule.get("then", {})
            if "fact" not in then or "value" not in then:
                raise ValueError("Bagian THEN pada rule derive harus menentukan 'fact' dan 'value'")

        elif rule_type == "adjust":
            then = rule.get("then", {})
            adjustments = then.get("adjust", {})
            if not adjustments or not isinstance(adjustments, dict):
                raise ValueError("Bagian THEN pada rule adjust harus memiliki dict 'adjust'")
            for inst in adjustments.keys():
                if inst not in INSTRUMENTS:
                    raise ValueError(f"Instrumen investasi '{inst}' tidak valid. Harus salah satu dari: {INSTRUMENTS}")

    def add_rule(self, rule: Dict[str, Any]) -> None:
        """Tambah rule baru (setelah divalidasi) dan simpan ke file."""
        self.validate_rule(rule, is_new=True)
        self.rules.append(rule)
        self.save()

    def update_rule(self, rule_id: str, new_rule: Dict[str, Any]) -> None:
        """Update rule yang ada dan simpan ke file."""
        self.validate_rule(new_rule, is_new=False)
        for i, r in enumerate(self.rules):
            if r["id"] == rule_id:
                self.rules[i] = new_rule
                self.save()
                return
        raise KeyError(f"Rule dengan ID '{rule_id}' tidak ditemukan")

    def delete_rule(self, rule_id: str) -> None:
        """Hapus rule berdasarkan ID dan simpan ke file."""
        if not self.get_rule(rule_id):
            raise KeyError(f"Rule dengan ID '{rule_id}' tidak ditemukan")
        self.data["rules"] = [r for r in self.rules if r["id"] != rule_id]
        self.save()
