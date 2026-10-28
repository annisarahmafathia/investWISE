"""Demo cepat inference engine lewat terminal (CLI).

Menjalankan pengujian forward chaining dengan fasilitas penjelasan HOW & WHY.
"""

import sys
import os

# Pastikan UTF-8 encoding di terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Pastikan root direktori terdaftar di sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.knowledge_base import KnowledgeBase
from core.inference_engine import InferenceEngine
from core.explanation import explain_how, explain_why

kb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "rules.json")
kb = KnowledgeBase(kb_path)
engine = InferenceEngine(kb)

kasus_uji = {
    "1. Mahasiswa Pemula (Konservatif)": {
        "inputs": dict(
            usia=21,
            pendapatan=2_000_000,
            tujuan="jangka_pendek",
            profil_user="konservatif",
            reaksi_turun="jual_semua",
            pengalaman="belum_ada",
            dana_darurat="belum"
        ),
        "modal": 1_500_000
    },
    "2. Karyawan Muda (Moderat)": {
        "inputs": dict(
            usia=27,
            pendapatan=8_000_000,
            tujuan="jangka_panjang",
            profil_user="moderat",
            reaksi_turun="tunggu",
            pengalaman="pernah",
            dana_darurat="ada"
        ),
        "modal": 10_000_000
    },
    "3. Profesional Berpengalaman (Agresif)": {
        "inputs": dict(
            usia=35,
            pendapatan=15_000_000,
            tujuan="jangka_panjang",
            profil_user="agresif",
            reaksi_turun="beli_lagi",
            pengalaman="berpengalaman",
            dana_darurat="ada"
        ),
        "modal": 25_000_000
    }
}

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  SISTEM PAKAR ALOKASI ASET INVESTASI PEMULA - MODE PENGUJIAN CLI")
    print("=" * 70)

    for nama, data in kasus_uji.items():
        print(f"\n>>> MENJALANKAN {nama.upper()}")
        print("-" * 70)
        res = engine.run(data["inputs"], modal_investasi=data["modal"])
        print(explain_how(kb, res))
        print("=" * 70)

    print("\nContoh Fasilitas Penjelasan (WHY):")
    print(explain_why(kb, "dana_darurat"))
    print(explain_why(kb, "reaksi_turun"))
    print("\n[OK] Pengujian CLI selesai dengan sukses!")
