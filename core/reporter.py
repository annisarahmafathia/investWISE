"""Modul Pelaporan (Reporting): Menghasilkan laporan PDF resmi dan ekspor data CSV."""

import io
import csv
from datetime import datetime
from typing import Dict, Any, List
from fpdf import FPDF
from core.inference_engine import INSTRUMENT_LABEL, ConsultationResult
from core.formatting import format_rupiah


class InvestmentReportPDF(FPDF):
    """Template PDF laporan rekomendasi alokasi investasi."""

    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(24, 43, 73)
        self.cell(self.epw, 7, "SISTEM PAKAR REKOMENDASI ALOKASI ASET INVESTASI", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 110, 120)
        self.cell(self.epw, 5, "Laporan Hasil Konsultasi & Alokasi Portofolio Investor Pemula", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(2)
        self.set_draw_color(200, 205, 215)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(self.epw, 10, f"Halaman {self.page_no()}/{{nb}} - Dicetak otomatis oleh InvestWise AI", align="C")


def generate_pdf_report(result: ConsultationResult, user_name: str = "Investor Pemula", modal: float = 0.0, kb=None) -> bytes:
    """Buat file PDF hasil konsultasi lengkap dan kembalikan sebagai byte stream."""
    pdf = InvestmentReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    epw = pdf.epw

    # Identitas Konsultasi
    pdf.set_fill_color(245, 248, 252)
    start_y = pdf.get_y()
    pdf.rect(pdf.l_margin, start_y, epw, 24, "F")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 41, 59)
    
    pdf.set_xy(pdf.l_margin + 4, start_y + 3)
    pdf.cell(epw / 2 - 4, 5, f"Nama Investor: {user_name}", new_x="RIGHT", new_y="TOP")
    pdf.cell(epw / 2 - 4, 5, f"Tanggal: {datetime.now().strftime('%d %B %Y, %H:%M WIB')}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(pdf.l_margin + 4)
    modal_str = format_rupiah(modal) if modal > 0 else "Belum dispesifikasikan"
    pdf.cell(epw / 2 - 4, 5, f"Modal Rencana: {modal_str}", new_x="RIGHT", new_y="TOP")
    pdf.cell(epw / 2 - 4, 5, "Metode: Forward Chaining + Certainty Factor", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(start_y + 28)

    # 1. Hasil Diagnosa Utama
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(16, 120, 80)
    pdf.cell(epw, 6, "1. HASIL DIAGNOSA PROFIL RISIKO", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    profil_text = result.profile.upper()
    confidence_pct = f"{result.confidence:.1%}"
    pdf.cell(epw, 5, f"Profil Risiko Anda: {profil_text} (Tingkat Kepercayaan / CF: {confidence_pct})", new_x="LMARGIN", new_y="NEXT")

    if kb and result.profile in kb.profile_info:
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(epw, 4.5, f"Karakteristik: {kb.profile_info[result.profile]}")
    pdf.ln(3)

    # 2. Tabel Rekomendasi Alokasi
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(epw, 6, "2. REKOMENDASI ALOKASI PORTOFOLIO", new_x="LMARGIN", new_y="NEXT")

    # Header Tabel
    col1_w = epw * 0.45
    col2_w = epw * 0.20
    col3_w = epw * 0.35

    pdf.set_fill_color(226, 232, 240)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(col1_w, 6.5, "Instrumen Investasi", border=1, fill=True)
    pdf.cell(col2_w, 6.5, "Porsi (%)", border=1, align="C", fill=True)
    pdf.cell(col3_w, 6.5, "Nominal Estimasi (Rp)", border=1, align="R", fill=True, new_x="LMARGIN", new_y="NEXT")

    # Isi Tabel
    pdf.set_font("Helvetica", "", 8.5)
    for inst, pct in result.allocation.items():
        label = INSTRUMENT_LABEL.get(inst, inst)
        nom_val = result.nominal_allocation.get(inst, 0)
        nom_text = format_rupiah(nom_val) if modal > 0 else "-"

        pdf.cell(col1_w, 6, f" {label}", border=1)
        pdf.cell(col2_w, 6, f"{pct}%", border=1, align="C")
        pdf.cell(col3_w, 6, f"{nom_text} ", border=1, align="R", new_x="LMARGIN", new_y="NEXT")

    # Total Row
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(col1_w, 6, " Total Alokasi", border=1)
    pdf.cell(col2_w, 6, "100%", border=1, align="C")
    nom_total = format_rupiah(modal) if modal > 0 else "-"
    pdf.cell(col3_w, 6, f"{nom_total} ", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # 3. Penjelasan Reasoning HOW
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(epw, 6, "3. PENJELASAN ATURAN SISTEM PAKAR (EXPLANATION FACILITY)", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(51, 65, 85)
    for i, rid in enumerate(result.fired_rules, 1):
        rule = kb.get_rule(rid) if kb else None
        if rule:
            cond = " AND ".join(f"{c['fact']} {c['op']} {c['value']}" for c in rule["if"])
            source = f" [{rule.get('source', 'Pakar')}]"
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(epw, 4.5, f"{i}. Rule {rid}: IF {cond} THEN {rule.get('description', '')}{source}")
    pdf.ln(3)

    # Peringatan Keuangan
    if result.warnings:
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(220, 38, 38)
        pdf.cell(epw, 5, "CATATAN PENTING & PERINGATAN RISIKO:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(51, 65, 85)
        for w in result.warnings:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(epw, 4.5, f"- {w}")
        pdf.ln(3)

    # Disclaimer
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(140, 140, 140)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        epw, 4,
        "Disclaimer: Laporan ini diterbitkan secara otomatis oleh Sistem Pakar AI untuk tujuan edukasi keuangan. "
        "Keputusan investasi sepenuhnya merupakan tanggung jawab pribadi pemodal. Pastikan memahami profil risiko sebelum bertransaksi."
    )

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def generate_csv_report(result: ConsultationResult, user_name: str = "Investor Pemula", modal: float = 0.0) -> str:
    """Buat representasi string format CSV untuk ekspor spreadsheet."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Parameter", "Nilai"])
    writer.writerow(["Nama Investor", user_name])
    writer.writerow(["Tanggal Konsultasi", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["Profil Risiko Terpilih", result.profile.upper()])
    writer.writerow(["Tingkat Kepercayaan (CF)", f"{result.confidence:.2%}"])
    writer.writerow(["Modal Rencana (Rp)", modal])
    writer.writerow([])
    writer.writerow(["Instrumen Investasi", "Persentase (%)", "Nominal Estimasi (Rp)"])
    for inst, pct in result.allocation.items():
        nom = result.nominal_allocation.get(inst, 0) if modal > 0 else 0
        writer.writerow([INSTRUMENT_LABEL.get(inst, inst), f"{pct}%", nom])
    writer.writerow(["Total Modal", f"{sum(result.allocation.values())}%", round(modal) if modal > 0 else 0])
    return output.getvalue()
