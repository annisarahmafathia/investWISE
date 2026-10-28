"""Working memory: menyimpan fakta, evidence hipotesis, rule yang aktif, dan jejak penalaran."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


@dataclass
class Fact:
    """Satu fakta di working memory."""
    name: str
    value: Any
    cf: float = 1.0
    origin: str = "user"  # "user" atau ID rule yang menurunkannya


@dataclass
class Evidence:
    """Bukti (hasil satu rule) yang mendukung sebuah hipotesis."""
    rule_id: str
    hypothesis: str
    cf: float


class WorkingMemory:
    """Memori kerja dinamis yang diperbarui selama proses penalaran inferensi."""

    def __init__(self):
        self.facts: Dict[str, Fact] = {}           # nama_fakta -> Fact
        self.evidences: Dict[str, List[Evidence]] = {}  # hipotesis -> list[Evidence]
        self.fired: List[str] = []                 # ID rule yang sudah dieksekusi (berurutan)
        self.trace: List[Tuple[str, str]] = []     # list of (fase, deskripsi_langkah)

    def add_fact(self, name: str, value: Any, cf: float = 1.0, origin: str = "user") -> None:
        """Tambah atau perbarui fakta di working memory."""
        self.facts[name] = Fact(name, value, cf, origin)

    def get(self, name: str) -> Optional[Fact]:
        """Ambil objek Fact berdasarkan nama, atau None bila belum ada."""
        return self.facts.get(name)

    def add_evidence(self, hypothesis: str, rule_id: str, cf: float) -> None:
        """Catat evidence pendukung untuk suatu hipotesis profil."""
        self.evidences.setdefault(hypothesis, []).append(Evidence(rule_id, hypothesis, cf))

    def mark_fired(self, rule_id: str) -> None:
        """Tandai rule sudah dieksekusi agar tidak terjadi firing berulang."""
        if rule_id not in self.fired:
            self.fired.append(rule_id)

    def has_fired(self, rule_id: str) -> bool:
        """Cek apakah rule sudah dieksekusi."""
        return rule_id in self.fired

    def log(self, phase: str, text: str) -> None:
        """Catat satu langkah reasoning step-by-step ke trace penalaran."""
        self.trace.append((phase, text))

    def reset(self) -> None:
        """Bersihkan seluruh isi working memory."""
        self.facts.clear()
        self.evidences.clear()
        self.fired.clear()
        self.trace.clear()
