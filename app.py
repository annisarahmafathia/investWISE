"""Aplikasi Web Sistem Pakar Rekomendasi Alokasi Aset Investasi bagi Investor Pemula.

Dibangun dengan Streamlit, mengintegrasikan:
- Forward Chaining Inference Engine
- Certainty Factor (CF)
- Dynamic Working Memory
- Explanation Facility (WHY & HOW)
- Knowledge Acquisition (CRUD Rules)
- Riwayat, Statistik, Pencarian & Filter
- Ekspor Laporan PDF & CSV
"""

import os
import base64
import sys
import json
import streamlit as st
import pandas as pd
import altair as alt

# Pastikan root direktori terdaftar di sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
LOGO_PATH = os.path.join(BASE_DIR, "assets", "investwise-logo.png")
FAVICON_PATH = os.path.join(BASE_DIR, "assets", "investwise-favicon.png")
with open(LOGO_PATH, "rb") as logo_file:
    LOGO_DATA_URI = "data:image/png;base64," + base64.b64encode(logo_file.read()).decode("ascii")

from core.knowledge_base import KnowledgeBase
from core.inference_engine import InferenceEngine, INSTRUMENT_LABEL
from core.explanation import explain_why, explain_how
from core.history_manager import HistoryManager
from core.reporter import generate_pdf_report, generate_csv_report
from core.formatting import format_rupiah
from core.allocations import allocate_nominal

# ==================== KONFIGURASI HALAMAN ====================
st.set_page_config(
    page_title="InvestWise AI - Sistem Pakar Alokasi Aset",
    page_icon=FAVICON_PATH,
    layout="wide",
    initial_sidebar_state="auto"
)

# Palet referensi: pale lime, electric lime, dan deep teal.
st.markdown("""
<style>
    :root { --deep:#00545f; --lime:#d6fb00; --pale:#ecffb6; --ink:#073c43; --muted:#537078; --line:#dbe8d5; --paper:#f5f9ec; }
    .stApp { background:radial-gradient(circle at 83% 1%, #edffc4 0, transparent 30rem), var(--paper); color:var(--ink); }
    [data-testid="stHeader"] { background:rgba(245,249,236,.91); }
    .main .block-container { max-width:1280px; padding-top:1.25rem; padding-bottom:3rem; }
    html, body, body * { cursor:default; }
    input:not([type="button"]):not([type="submit"]):not([type="checkbox"]):not([type="radio"]), textarea, [contenteditable="true"] { cursor:text; }
    button, a, summary, select, [role="button"], [role="combobox"], [role="slider"], [role="checkbox"], [role="radio"] { cursor:pointer; }
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stDateInput"] input, [data-testid="stTimeInput"] input { color:rgba(7,60,67,.62)!important; caret-color:var(--deep); }
    [data-testid="stTextInput"] input::placeholder, [data-testid="stNumberInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder, [data-testid="stDateInput"] input::placeholder, [data-testid="stTimeInput"] input::placeholder { color:rgba(7,60,67,.38)!important; opacity:1; }
    [data-testid="stSelectbox"] [role="combobox"], [data-testid="stMultiSelect"] [role="combobox"] { color:rgba(7,60,67,.62)!important; }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] { color:rgba(7,60,67,.62)!important; }
    h1,h2,h3 { color:var(--ink); letter-spacing:-.025em; }
    [data-testid="stSidebar"] { background:var(--deep); border-right:1px solid #00454e; }
    .sidebar-brand { display:flex; align-items:center; gap:.8rem; margin:.3rem 0 1.35rem; }
    .sidebar-brand-mark { width:58px; height:50px; flex:none; display:flex; align-items:center; justify-content:center; padding:5px; border-radius:14px; background:#fff; box-shadow:0 7px 18px rgba(0,0,0,.12); }
    .sidebar-brand-mark img { display:block; width:100%; height:100%; object-fit:contain; }
    .sidebar-brand-name { color:#fff; font-size:1.1rem; font-weight:720; letter-spacing:-.03em; line-height:1.1; }
    .sidebar-brand-caption { color:#cbe8d8; font-size:.75rem; line-height:1.4; margin-top:.2rem; }
    .sidebar-section { color:var(--pale); font-size:.7rem; font-weight:750; letter-spacing:.12em; margin:.75rem 0 .45rem; }
    .sidebar-note { border:1px solid rgba(236,255,182,.4); background:rgba(236,255,182,.12); border-radius:18px; padding:1rem; margin-top:1.25rem; }
    .sidebar-note strong { color:#fff; font-size:.88rem; }
    .sidebar-note p { color:#d9efdf; font-size:.8rem; line-height:1.5; margin:.35rem 0 0; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:#cbe8d8; }
    [data-testid="stSidebar"] .stButton>button { justify-content:flex-start; text-align:left; width:100%; min-height:2.75rem; border-radius:13px; padding:.5rem .8rem; font-size:.91rem; margin-bottom:.17rem; }
    [data-testid="stSidebar"] .stButton>button[kind="tertiary"] { color:#f1ffdf; background:transparent; }
    [data-testid="stSidebar"] .stButton>button[kind="tertiary"]:hover { color:#fff; background:rgba(236,255,182,.15); }
    [data-testid="stSidebar"] .stButton>button[kind="primary"] { color:var(--deep); background:var(--lime); border-color:var(--lime); box-shadow:0 7px 15px rgba(0,0,0,.15); }
    .header-box { position:relative; overflow:hidden; color:#fff; padding:2rem 2.25rem; margin-bottom:1.1rem; border-radius:26px; background:linear-gradient(118deg,#00545f 0%,#006975 76%,#0c7a7f 100%); min-height:212px; box-shadow:0 17px 35px rgba(0,84,95,.12); }
    .header-box h1 { position:relative; z-index:1; color:#fff!important; margin:0; max-width:760px; font-size:2rem; font-weight:680; line-height:1.17; }
    .header-box p { position:relative; z-index:1; color:#d5eee4; margin:.65rem 0 0; max-width:650px; font-size:.95rem; line-height:1.55; }
    .eyebrow { position:relative; z-index:1; color:var(--lime); font-size:.7rem; font-weight:750; letter-spacing:.16em; margin-bottom:.8rem; }
    .header-box::before { content:""; position:absolute; right:3.7rem; top:50%; transform:translateY(-50%); width:155px; height:155px; border-radius:50%; border:1px solid rgba(236,255,182,.7); box-shadow:0 0 0 27px rgba(236,255,182,.09),0 0 0 56px rgba(236,255,182,.05); }
    .header-box::after { content:""; position:absolute; right:6.3rem; top:50%; transform:translateY(-50%); width:74px; height:74px; border-radius:50%; background:var(--lime); box-shadow:0 0 0 14px rgba(214,251,0,.15); }
    .feature-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.8rem; margin:0 0 1.25rem; }
    .feature-card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1rem 1.1rem; min-height:116px; box-shadow:0 5px 18px rgba(0,84,95,.035); }
    .feature-card b { display:block; color:var(--deep); font-size:.88rem; margin:.35rem 0 .18rem; }
    .feature-card p { color:var(--muted); font-size:.79rem; line-height:1.45; margin:0; }
    .feature-icon { display:inline-grid; place-items:center; width:27px; height:27px; border-radius:9px; background:var(--pale); color:var(--deep); font-family:'Material Symbols Rounded'; font-size:18px; line-height:1; }
    .empty-panel { background:#fff; border:1px solid var(--line); border-radius:22px; padding:1.45rem 1.6rem; margin-bottom:.8rem; }
    .empty-panel h3 { color:var(--deep); font-size:1.1rem; margin:.35rem 0; }
    .empty-panel p { color:var(--muted); font-size:.88rem; line-height:1.5; margin:0; }
    .badge-konservatif,.badge-moderat,.badge-agresif { padding:7px 14px; border-radius:999px; font-weight:650; display:inline-block; font-size:.91rem; }
    .badge-konservatif { background:var(--pale); color:var(--deep); }
    .badge-moderat { background:var(--lime); color:var(--deep); }
    .badge-agresif { background:var(--deep); color:#fff; }
    .st-key-risk-card { background:var(--deep); color:#fff!important; border-radius:20px; padding:1.15rem 1.3rem; }
    .st-key-risk-card [data-testid="stMarkdownContainer"] * { color:#fff!important; }
    .st-key-risk-card [data-testid="stCaptionContainer"] { color:#e0f4d7!important; }
    [data-testid="stMetric"], [data-testid="stForm"] { background:#fff; border:1px solid var(--line); border-radius:18px; }
    [data-testid="stMetric"] { padding:.9rem 1rem; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { font-size:1.35rem; white-space:normal; overflow-wrap:anywhere; line-height:1.3; }
    [data-testid="stWidgetLabel"] p { font-size:.91rem; font-weight:550; }
    [data-testid="stCaptionContainer"] p { font-size:.8rem; }
    [data-testid="stForm"] { padding:1.2rem; }
    [data-testid="stExpander"], [data-testid="stDataFrame"] { border-radius:16px; }
    .stButton>button, [data-testid="stDownloadButton"] button, [data-testid="stFormSubmitButton"] button { border-radius:999px; font-weight:650; min-height:2.75rem; }
    .stButton>button[kind="primary"], [data-testid="stDownloadButton"] button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] { background:var(--deep); border-color:var(--deep); color:#fff; }
    .stButton>button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button[kind="primary"]:hover { background:#00707a; border-color:#00707a; }
    .stButton>button:focus-visible, [data-testid="stSidebar"] button:focus-visible { outline:3px solid var(--lime); outline-offset:2px; }
    @media (max-width:850px) { .header-box::before,.header-box::after { opacity:.25; right:-20px; } }
    @media (max-width:700px) { .main .block-container { padding:1rem 1rem 2rem; } .header-box { padding:1.45rem; min-height:unset; border-radius:21px; } .header-box h1 { font-size:1.65rem; } .header-box::before,.header-box::after { display:none; } .feature-grid { grid-template-columns:1fr; gap:.55rem; } .feature-card { min-height:unset; } }
</style>
""", unsafe_allow_html=True)


# ==================== LOAD BACKEND ====================
@st.cache_resource
def get_system():
    kb_path = os.path.join(BASE_DIR, "data", "rules.json")
    history_path = os.path.join(BASE_DIR, "data", "consultation_history.json")
    kb = KnowledgeBase(kb_path)
    engine = InferenceEngine(kb)
    history_mgr = HistoryManager(history_path)
    return kb, engine, history_mgr

kb, engine, history_mgr = get_system()

# Load instrumen ensiklopedia
instruments_path = os.path.join(BASE_DIR, "data", "instruments.json")
instruments_data = []
if os.path.exists(instruments_path):
    with open(instruments_path, "r", encoding="utf-8") as f:
        instruments_data = json.load(f)

INSTRUMENT_ICONS = {
    "reksa_dana": ":material/savings:",
    "obligasi": ":material/account_balance:",
    "emas": ":material/diamond:",
    "saham": ":material/monitoring:",
}


# ==================== SIDEBAR NAVIGASI ====================
st.sidebar.markdown(f"""
<div class="sidebar-brand">
  <div class="sidebar-brand-mark"><img src="{LOGO_DATA_URI}" alt="Logo InvestWise"></div>
  <div><div class="sidebar-brand-name">InvestWise</div>
  <div class="sidebar-brand-caption">Sistem pakar investasi</div></div>
</div>
""", unsafe_allow_html=True)

nav_groups = [
    ("MULAI", [
        ("Konsultasi Investasi", ":material/edit_note:"),
        ("Hasil & Analisis", ":material/analytics:"),
    ]),
    ("JELAJAHI", [
        ("Ensiklopedia Instrumen", ":material/menu_book:"),
        ("Riwayat & Statistik", ":material/history:"),
    ]),
    ("KELOLA", [
        ("Basis Pengetahuan", ":material/account_tree:"),
    ]),
]

if "active_menu" not in st.session_state:
    st.session_state.active_menu = "Konsultasi Investasi"


def select_menu(name: str) -> None:
    """Pindahkan halaman aktif saat tombol navigasi dipilih."""
    st.session_state.active_menu = name


for group_name, links in nav_groups:
    st.sidebar.markdown(f'<div class="sidebar-section">{group_name}</div>', unsafe_allow_html=True)
    for label, icon in links:
        st.sidebar.button(
            label,
            key=f"nav_{label}",
            icon=icon,
            type="primary" if st.session_state.active_menu == label else "tertiary",
            width="stretch",
            on_click=select_menu,
            args=(label,),
        )

st.sidebar.markdown("""
<div class="sidebar-note">
  <strong>Mulai dari konsultasi</strong>
  <p>Isi profil Anda, lihat rekomendasi, lalu telusuri alasan di balik hasilnya.</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.caption("INF313 · Kecerdasan Artifisial")

menu = st.session_state.active_menu


# ==================== MENU 1: KONSULTASI INVESTASI ====================
if menu == "Konsultasi Investasi":
    st.markdown("""
    <div class="header-box">
        <div class="eyebrow">INVESTWISE / KONSULTASI</div>
        <h1>Rencanakan alokasi investasi</h1>
        <p>Isi profil singkat Anda untuk melihat rekomendasi aset beserta alasan di baliknya.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-grid">
      <div class="feature-card"><span class="feature-icon">person</span><b>01 / Kenali profil</b><p>Jawab pertanyaan singkat tentang tujuan dan kebiasaan investasi.</p></div>
      <div class="feature-card"><span class="feature-icon">hub</span><b>02 / Analisis aturan</b><p>Sistem menggabungkan aturan pakar dan tingkat keyakinan jawaban.</p></div>
      <div class="feature-card"><span class="feature-icon">donut_large</span><b>03 / Lihat alokasi</b><p>Terima pembagian aset beserta alasan dan rincian dananya.</p></div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_konsultasi"):
        st.subheader("01  Data dan rencana investasi", icon=":material/person_outline:")
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            nama_user = st.text_input("Nama Lengkap / Panggilan:", value="Investor Muda", help="Nama untuk dicantumkan di laporan")
        with col_u2:
            modal_investasi = st.number_input(
                "Rencana Modal yang Ingin Diinvestasikan (Rp):",
                min_value=0,
                max_value=1_000_000_000,
                value=5_000_000,
                step=500_000,
                help="Nominal dana yang dialokasikan ke instrumen investasi"
            )

        st.divider()
        st.subheader("02  Profil dan kebiasaan investasi", icon=":material/tune:")

        inputs = {}
        user_cfs = {}

        for q in kb.questions:
            qid = q["id"]
            label = q["label"]
            why_text = q.get("why", "")

            st.write(f"**{label}**")
            col_q, col_why = st.columns([3, 1])

            with col_q:
                if q["type"] == "number":
                    unit = q.get("unit", "")
                    inputs[qid] = st.number_input(
                        f"Masukkan {qid} ({unit}):",
                        min_value=q.get("min", 0),
                        max_value=q.get("max", 1000000000),
                        value=q.get("default", 25),
                        key=f"input_{qid}",
                        label_visibility="collapsed"
                    )
                elif q["type"] == "choice":
                    opts = list(q["options"].keys())
                    inputs[qid] = st.selectbox(
                        f"Pilih {qid}:",
                        options=opts,
                        format_func=lambda x, options=q["options"]: options[x],
                        index=opts.index(q.get("default", opts[0])),
                        key=f"input_{qid}",
                        label_visibility="collapsed"
                    )

            with col_why:
                with st.popover("Alasan", icon=":material/help_outline:"):
                    st.info(why_text, icon=":material/lightbulb:")

            # Jika pertanyaan memiliki CF keyakinan pengguna
            if q.get("has_cf", False):
                with st.expander(f"Keyakinan jawaban · {qid.replace('_', ' ')}", expanded=False, icon=":material/tune:"):
                    cf_val = st.slider(
                        "Seberapa yakin Anda dengan pilihan jawaban di atas? (1.0 = Sangat Yakin / 100%)",
                        min_value=0.1,
                        max_value=1.0,
                        value=1.0,
                        step=0.05,
                        key=f"cf_{qid}"
                    )
                    user_cfs[qid] = cf_val
            else:
                user_cfs[qid] = 1.0

            st.write("")

        submitted = st.form_submit_button("Jalankan analisis", width="stretch", type="primary", icon=":material/arrow_forward:")

    if submitted:
        try:
            with st.spinner("Mesin inferensi sedang mengeksekusi Forward Chaining & Certainty Factor..."):
                res = engine.run(inputs, user_cf=user_cfs, modal_investasi=modal_investasi)
                # Simpan ke session state
                st.session_state["consultation_result"] = res
                st.session_state["consultation_name"] = nama_user
                st.session_state["consultation_modal"] = modal_investasi

                # Simpan ke file riwayat
                history_mgr.add_entry(nama_user, res, inputs, modal=modal_investasi)

            st.success("Analisis profil dan alokasi portofolio selesai.", icon=":material/check_circle:")
            st.info("Buka menu **Hasil & Analisis** untuk melihat alokasi, rincian nominal, dan jejak penalaran.", icon=":material/info:")

        except Exception as e:
            st.error(f"Terjadi kesalahan saat inferensi: {e}", icon=":material/error:")


# ==================== MENU 2: HASIL & ANALISIS ====================
elif menu == "Hasil & Analisis":
    st.markdown("""
    <div class="header-box">
        <div class="eyebrow">INVESTWISE / RINGKASAN</div>
        <h1>Rekomendasi portofolio</h1>
        <p>Lihat profil risiko, pembagian aset, dan aturan yang digunakan sistem.</p>
    </div>
    """, unsafe_allow_html=True)

    if "consultation_result" not in st.session_state:
        st.markdown("""
        <div class="empty-panel">
          <span class="feature-icon">tips_and_updates</span>
          <h3>Mulai konsultasi untuk melihat portofolio Anda</h3>
          <p>Hasil akan menampilkan profil risiko, proporsi aset, estimasi nominal, dan alasan dari setiap aturan yang digunakan.</p>
        </div>
        <div class="feature-grid">
          <div class="feature-card"><span class="feature-icon">edit_note</span><b>Isi profil</b><p>Lengkapi pertanyaan dan rencana modal.</p></div>
          <div class="feature-card"><span class="feature-icon">psychology</span><b>Jalankan analisis</b><p>Sistem menghitung rekomendasi dari aturan pakar.</p></div>
          <div class="feature-card"><span class="feature-icon">analytics</span><b>Pelajari hasil</b><p>Lihat grafik, rincian dana, dan jejak penalaran.</p></div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Mulai konsultasi", type="primary", icon=":material/arrow_forward:", on_click=select_menu, args=("Konsultasi Investasi",))
    else:
        res = st.session_state["consultation_result"]
        user_name = st.session_state.get("consultation_name", "Investor")
        modal = st.session_state.get("consultation_modal", 0.0)
        # Hitung ulang agar sesi lama juga memakai nominal rupiah utuh yang totalnya tepat.
        res.nominal_allocation = allocate_nominal(res.allocation, modal)

        # Kartu Ringkasan Atas
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            with st.container(border=True, height="stretch"):
                st.caption("PROFIL RISIKO")
                badge_class = f"badge-{res.profile.lower()}"
                st.markdown(f"<span class='{badge_class}' style='font-size:18px'>{res.profile.upper()}</span>", unsafe_allow_html=True)
                st.caption(kb.profile_info.get(res.profile, ""))

        with col_r2:
            with st.container(border=True, height="stretch", key="risk-card"):
                st.caption("TINGKAT KEYAKINAN")
                st.markdown(f"<h2 style='color:#fff;margin:.1rem 0'>{res.confidence:.1%}</h2>", unsafe_allow_html=True)
                st.caption("Certainty Factor gabungan")

        with col_r3:
            with st.container(border=True, height="stretch"):
                st.caption("MODAL RENCANA")
                modal_text = format_rupiah(modal) if modal > 0 else "Belum ditentukan"
                st.markdown(f"<h2 style='color:#00545f;margin:.1rem 0'>{modal_text}</h2>", unsafe_allow_html=True)
                st.caption(f"Investor: {user_name}")

        # Peringatan Keuangan jika ada
        if res.warnings:
            for w in res.warnings:
                st.error(w, icon=":material/warning:")

        st.divider()

        # Visualisasi & Tabel Alokasi
        col_chart, col_table = st.columns([3, 2])

        with col_chart:
            st.subheader("Proporsi alokasi aset", icon=":material/donut_large:")
            df_chart = pd.DataFrame([
                {
                    "Instrumen": INSTRUMENT_LABEL.get(k, k),
                    "Persentase": v,
                    "Nominal (Rp)": format_rupiah(res.nominal_allocation.get(k, 0)) if modal > 0 else "-",
                }
                for k, v in res.allocation.items()
            ])

            pie = alt.Chart(df_chart).mark_arc(innerRadius=60, stroke="#ffffff").encode(
                theta=alt.Theta(field="Persentase", type="quantitative"),
                color=alt.Color(
                    field="Instrumen",
                    type="nominal",
                    scale=alt.Scale(range=["#00545f", "#d6fb00", "#6ba49d", "#b8d77c"])
                ),
                tooltip=["Instrumen", "Persentase", alt.Tooltip("Nominal (Rp)", title="Nominal")]
            ).properties(height=320)

            st.altair_chart(pie, width="stretch")

        with col_table:
            st.subheader("Rincian distribusi dana", icon=":material/table_chart:")
            rows = []
            for inst, pct in res.allocation.items():
                nom = res.nominal_allocation.get(inst, 0)
                rows.append({
                    "Instrumen Investasi": INSTRUMENT_LABEL.get(inst, inst),
                    "Porsi": f"{pct}%",
                    "Estimasi Nominal": format_rupiah(nom) if modal > 0 else "-"
                })
            total_porsi = sum(res.allocation.values())
            rows.append({
                "Instrumen Investasi": "Total Modal",
                "Porsi": f"{total_porsi}%",
                "Estimasi Nominal": format_rupiah(modal) if modal > 0 else "-",
            })
            df_display = pd.DataFrame(rows)
            st.dataframe(df_display, width="stretch", hide_index=True)

        st.divider()

        # Fasilitas Penjelasan HOW (Step by step reasoning)
        st.subheader("Cara sistem menentukan hasil", icon=":material/psychology:")
        with st.expander("Aturan yang digunakan", expanded=True, icon=":material/rule:"):
            for i, rid in enumerate(res.fired_rules, 1):
                rule = kb.get_rule(rid)
                if rule:
                    cf_info = f" • Certainty Factor: **{rule.get('cf', 1.0):.2f}**" if "cf" in rule else ""
                    st.markdown(f"""
                    **{i}. Rule `{rid}` ({rule.get('type', 'rule').upper()})**{cf_info}
                    - **Deskripsi:** {rule.get('description', '-')}
                    - **Sumber Rujukan:** *{rule.get('source', 'Pakar')}*
                    """)

        with st.expander("Jejak penalaran", expanded=False, icon=":material/route:"):
            for i, (phase, text) in enumerate(res.trace, 1):
                st.code(f"Step {i:02d} [{phase}]: {text}", language="markdown")

        # Tombol Download PDF & CSV
        st.divider()
        st.subheader("Unduh laporan", icon=":material/download:")
        col_dl1, col_dl2 = st.columns(2)

        with col_dl1:
            pdf_bytes = generate_pdf_report(res, user_name=user_name, modal=modal, kb=kb)
            st.download_button(
                label="Unduh laporan PDF",
                data=pdf_bytes,
                file_name=f"Laporan_Investasi_{user_name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                width="stretch",
                type="primary",
                icon=":material/picture_as_pdf:"
            )

        with col_dl2:
            csv_str = generate_csv_report(res, user_name=user_name, modal=modal)
            st.download_button(
                label="Unduh ringkasan CSV",
                data=csv_str,
                file_name=f"Data_Investasi_{user_name.replace(' ', '_')}.csv",
                mime="text/csv",
                width="stretch",
                icon=":material/table_view:"
            )


# ==================== MENU 3: ENSIKLOPEDIA INSTRUMEN ====================
elif menu == "Ensiklopedia Instrumen":
    st.markdown("""
    <div class="header-box">
        <div class="eyebrow">INVESTWISE / KATALOG</div>
        <h1>Kenali instrumen investasi</h1>
        <p>Bandingkan karakteristik, potensi imbal hasil, dan risiko setiap instrumen.</p>
    </div>
    """, unsafe_allow_html=True)

    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_inst = st.text_input("Cari instrumen", placeholder="Contoh: obligasi, reksa dana, dividen...", icon=":material/search:")
    with col_filter:
        cat_filter = st.selectbox("Kategori", ["Semua", "Likuiditas", "Pendapatan Tetap", "Lindung Nilai", "Ekuitas"])

    filtered_inst = instruments_data
    if search_inst:
        q = search_inst.lower()
        filtered_inst = [
            i for i in filtered_inst
            if q in i["name"].lower() or q in i["description"].lower() or any(q in adv.lower() for adv in i.get("advantages", []))
        ]
    category_terms = {
        "Likuiditas": ("likuiditas", "rendah risiko"),
        "Pendapatan Tetap": ("pendapatan tetap", "fixed income"),
        "Lindung Nilai": ("lindung nilai", "hedging", "safe haven"),
        "Ekuitas": ("ekuitas", "capital growth"),
    }
    if cat_filter != "Semua":
        filtered_inst = [
            item for item in filtered_inst
            if any(term in item.get("category", "").lower() for term in category_terms[cat_filter])
        ]

    st.caption(f"Menampilkan {len(filtered_inst)} dari {len(instruments_data)} instrumen.")
    if not filtered_inst:
        st.info("Tidak ada instrumen yang cocok. Coba ubah kata kunci atau kategori.", icon=":material/search_off:")

    for item in filtered_inst:
        with st.expander(
            f"{item['name']} · Risiko {item['risk_level']}",
            expanded=False,
            icon=INSTRUMENT_ICONS.get(item["id"], ":material/account_balance_wallet:"),
        ):
            col_d1, col_d2, col_d3 = st.columns(3)
            for col, label, value in zip(
                (col_d1, col_d2, col_d3),
                ("Perkiraan imbal hasil", "Likuiditas", "Minimal investasi"),
                (item["expected_return"], item["liquidity"], item["min_investment"]),
            ):
                with col:
                    with st.container(border=True, height="stretch"):
                        st.caption(label)
                        st.markdown(f"**{value}**")

            st.write(f"**Kesesuaian Pemodal:** {item['suitability']}")
            st.write(item["description"])

            col_adv, col_dis = st.columns(2)
            with col_adv:
                st.markdown("**Keunggulan**")
                for adv in item.get("advantages", []):
                    st.markdown(f"- {adv}")
            with col_dis:
                st.markdown("**Risiko dan keterbatasan**")
                for dis in item.get("disadvantages", []):
                    st.markdown(f"- {dis}")


# ==================== MENU 4: RIWAYAT & STATISTIK ====================
elif menu == "Riwayat & Statistik":
    st.markdown("""
    <div class="header-box">
        <div class="eyebrow">INVESTWISE / AKTIVITAS</div>
        <h1>Riwayat dan statistik</h1>
        <p>Tinjau konsultasi sebelumnya dan pola penggunaan aturan sistem.</p>
    </div>
    """, unsafe_allow_html=True)

    stats = history_mgr.get_statistics()

    # Metrik Statistik
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Total sesi konsultasi", stats["total_sessions"], icon=":material/receipt_long:")
    col_s2.metric("Rata-rata tingkat CF", f"{stats['avg_confidence']:.1%}", icon=":material/verified:")
    col_s3.metric("Profil terbanyak", max(stats["profile_counts"], key=stats["profile_counts"].get).upper() if stats["total_sessions"] > 0 else "-", icon=":material/person:")
    col_s4.metric("Rata-rata rencana modal", format_rupiah(stats["avg_modal"]) if stats["total_sessions"] > 0 else "-", icon=":material/payments:")

    st.divider()

    col_stat_chart, col_stat_rules = st.columns([1, 1])

    with col_stat_chart:
        st.subheader("Distribusi profil risiko", icon=":material/bar_chart:")
        df_prof = pd.DataFrame([
            {"Profil": k.upper(), "Jumlah": v}
            for k, v in stats["profile_counts"].items()
        ])
        chart_prof = alt.Chart(df_prof).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
            x=alt.X("Profil:N", title="Profil Risiko"),
            y=alt.Y("Jumlah:Q", title="Frekuensi"),
            color=alt.Color("Profil:N", scale=alt.Scale(range=["#00545f", "#75a49b", "#d6fb00"]))
        ).properties(height=280)
        st.altair_chart(chart_prof, width="stretch")

    with col_stat_rules:
        st.subheader("Aturan yang paling sering digunakan", icon=":material/rule:")
        top_rules = list(stats["rule_frequency"].items())[:7]
        if top_rules:
            df_rules = pd.DataFrame(top_rules, columns=["ID Rule", "Frekuensi"]).sort_values("Frekuensi", ascending=True)
            chart_r = alt.Chart(df_rules).mark_bar(color="#00545f").encode(
                x=alt.X("Frekuensi:Q"),
                y=alt.Y("ID Rule:N", sort="-x")
            ).properties(height=280)
            st.altair_chart(chart_r, width="stretch")
        else:
            st.info("Belum ada data rule yang teraktivasi.", icon=":material/info:")

    st.divider()
    st.subheader("Riwayat konsultasi", icon=":material/history:")

    col_fil1, col_fil2 = st.columns([2, 1])
    with col_fil1:
        q_history = st.text_input("Cari nama atau ID konsultasi", icon=":material/search:")
    with col_fil2:
        prof_filter = st.selectbox("Profil risiko", ["Semua", "konservatif", "moderat", "agresif"])

    filtered_history = history_mgr.filter_history(profile=prof_filter, search_query=q_history)

    if filtered_history:
        display_data = []
        for h in filtered_history:
            display_data.append({
                "ID Sesi": h.get("id"),
                "Waktu": h.get("timestamp"),
                "Nama Pemodal": h.get("user_name"),
                "Profil Terpilih": h.get("profile", "").upper(),
                "Certainty Factor": f"{h.get('confidence', 0):.1%}",
                "Modal Rencana": format_rupiah(h.get("modal", 0)) if h.get("modal") else "-",
                "Rules Terpicu": ", ".join(h.get("fired_rules", []))
            })
        st.dataframe(pd.DataFrame(display_data), width="stretch", hide_index=True)
    else:
        st.info("Tidak ada riwayat yang cocok dengan kriteria pencarian.", icon=":material/search_off:")


# ==================== MENU 5: KNOWLEDGE ACQUISITION ====================
elif menu == "Basis Pengetahuan":
    st.markdown("""
    <div class="header-box">
        <div class="eyebrow">INVESTWISE / ATURAN</div>
        <h1>Kelola basis pengetahuan</h1>
        <p>Lihat, tambah, ubah, dan hapus aturan IF–THEN yang digunakan sistem.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_view, tab_add, tab_edit, tab_del = st.tabs([
        "Lihat aturan",
        "Tambah aturan",
        "Edit aturan",
        "Hapus aturan"
    ])

    # --- TAB 1: LIHAT & CARI RULES ---
    with tab_view:
        search_r = st.text_input("Cari aturan", placeholder="Cari ID, kondisi, atau sumber...", icon=":material/search:")
        rules_to_show = kb.search_rules(search_r) if search_r else kb.rules

        st.caption(f"Menampilkan {len(rules_to_show)} dari {len(kb.rules)} rules dalam sistem.")

        for r in rules_to_show:
            with st.expander(f"Rule `{r['id']}` [{r['type'].upper()}] — {r.get('description', '')}", icon=":material/rule:"):
                col_r_left, col_r_right = st.columns([2, 1])
                with col_r_left:
                    conds = " AND ".join(f"`{c['fact']} {c['op']} {c['value']}`" for c in r["if"])
                    st.markdown(f"**IF:** {conds}")
                    st.markdown(f"**THEN:** `{json.dumps(r['then'])}`")
                    if "warning" in r:
                        st.warning(r["warning"], icon=":material/warning:")
                with col_r_right:
                    if "cf" in r:
                        st.metric("Certainty Factor pakar", f"{r['cf']:.2f}", icon=":material/verified:")
                    st.write(f"**Sumber:** *{r.get('source', '-')}*")

    # --- TAB 2: TAMBAH RULE BARU ---
    with tab_add:
        st.subheader("Tambah aturan baru", icon=":material/add_circle:")
        with st.form("form_add_rule"):
            col_a1, col_a2 = st.columns(2)
            new_id = col_a1.text_input("ID Rule Baru (Unik):", placeholder="Misal: R16, D7, A4")
            new_type = col_a2.selectbox("Tipe Rule:", ["profile", "derive", "adjust"])

            new_desc = st.text_input("Deskripsi Singkat:", placeholder="Penjelasan aturan...")
            new_source = st.text_input("Sumber Literatur / Otoritas Pakar:", placeholder="Contoh: POJK No. 43/2015, Harry Markowitz MPT")

            st.markdown("**Kondisi Antecedent (IF):**")
            col_c1, col_c2, col_c3 = st.columns(3)
            c_fact = col_c1.selectbox("Fakta Parameter:", ["usia", "pendapatan", "tujuan", "reaksi_turun", "pengalaman", "dana_darurat", "kategori_usia", "kategori_pendapatan"])
            c_op = col_c2.selectbox("Operator:", ["==", "!=", "<", "<=", ">", ">="])
            c_val = col_c3.text_input("Nilai yang Dibandingkan:", placeholder="angka atau string")

            st.markdown("**Konsekuensi (THEN):**")
            if new_type == "profile":
                col_th1, col_th2 = st.columns(2)
                t_hyp = col_th1.selectbox("Hipotesis Profil:", ["konservatif", "moderat", "agresif"])
                t_cf = col_th2.slider("Certainty Factor Pakar (0.1 - 1.0):", 0.1, 1.0, 0.7, 0.05)
            elif new_type == "derive":
                col_th1, col_th2 = st.columns(2)
                t_fact = col_th1.text_input("Nama Fakta Baru:", placeholder="Contoh: status_karyawan")
                t_val = col_th2.text_input("Nilai Fakta Baru:", placeholder="Contoh: tetap")
            else:
                st.write("Penyesuaian Persentase Alokasi (%):")
                col_adj1, col_adj2, col_adj3, col_adj4 = st.columns(4)
                adj_rd = col_adj1.number_input("Reksa Dana", -50, 50, 0, 5)
                adj_ob = col_adj2.number_input("Obligasi", -50, 50, 0, 5)
                adj_em = col_adj3.number_input("Emas", -50, 50, 0, 5)
                adj_sh = col_adj4.number_input("Saham", -50, 50, 0, 5)

            btn_save_rule = st.form_submit_button("Validasi dan simpan aturan", type="primary", icon=":material/save:")

            if btn_save_rule:
                try:
                    # Parse nilai kondisi
                    val_parsed = c_val
                    if c_val.isdigit():
                        val_parsed = int(c_val)
                    elif c_val.replace(".", "", 1).isdigit():
                        val_parsed = float(c_val)

                    rule_payload = {
                        "id": new_id.strip(),
                        "type": new_type,
                        "if": [{"fact": c_fact, "op": c_op, "value": val_parsed}],
                        "source": new_source.strip() or "Heuristik Pakar Internal",
                        "description": new_desc.strip() or f"Rule {new_id}"
                    }

                    if new_type == "profile":
                        rule_payload["then"] = {"hypothesis": t_hyp}
                        rule_payload["cf"] = t_cf
                    elif new_type == "derive":
                        rule_payload["then"] = {"fact": t_fact.strip(), "value": t_val.strip()}
                    else:
                        adj_dict = {}
                        if adj_rd != 0: adj_dict["reksa_dana"] = adj_rd
                        if adj_ob != 0: adj_dict["obligasi"] = adj_ob
                        if adj_em != 0: adj_dict["emas"] = adj_em
                        if adj_sh != 0: adj_dict["saham"] = adj_sh
                        rule_payload["then"] = {"adjust": adj_dict}

                    kb.add_rule(rule_payload)
                    st.success(f"Rule '{new_id}' berhasil divalidasi dan disimpan ke data/rules.json!", icon=":material/check_circle:")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Gagal menyimpan rule: {ex}", icon=":material/error:")

    # --- TAB 3: EDIT RULE EKSISTING ---
    with tab_edit:
        st.subheader("Edit aturan", icon=":material/edit:")
        rule_ids = [r["id"] for r in kb.rules]
        selected_id = st.selectbox("Pilih Rule yang Ingin Diedit:", rule_ids)
        target_rule = kb.get_rule(selected_id)

        if target_rule:
            with st.form("form_edit_rule"):
                edit_desc = st.text_input("Deskripsi:", value=target_rule.get("description", ""))
                edit_source = st.text_input("Sumber Literatur:", value=target_rule.get("source", ""))
                edit_cf = None
                if "cf" in target_rule:
                    edit_cf = st.slider("Certainty Factor Pakar:", 0.1, 1.0, float(target_rule["cf"]), 0.05)

                btn_update = st.form_submit_button("Simpan perubahan", icon=":material/save:")
                if btn_update:
                    try:
                        updated_r = dict(target_rule)
                        updated_r["description"] = edit_desc
                        updated_r["source"] = edit_source
                        if edit_cf is not None:
                            updated_r["cf"] = edit_cf
                        kb.update_rule(selected_id, updated_r)
                        st.success(f"Rule '{selected_id}' berhasil diperbarui!", icon=":material/check_circle:")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Gagal memperbarui rule: {err}", icon=":material/error:")

    # --- TAB 4: HAPUS RULE ---
    with tab_del:
        st.subheader("Hapus aturan", icon=":material/delete:")
        del_id = st.selectbox("Pilih ID Rule yang Akan Dihapus:", [r["id"] for r in kb.rules], key="select_del")
        st.warning(f"Tindakan ini akan menghapus Rule `{del_id}` secara permanen dari file JSON basis pengetahuan.", icon=":material/warning:")

        if st.button("Hapus aturan", type="primary", icon=":material/delete:"):
            try:
                kb.delete_rule(del_id)
                st.success(f"Rule '{del_id}' berhasil dihapus!", icon=":material/check_circle:")
                st.rerun()
            except Exception as e_del:
                st.error(f"Gagal menghapus rule: {e_del}", icon=":material/error:")
