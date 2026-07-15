# -*- coding: utf-8 -*-
"""lib/ui.py — sistem desain & komponen bersama (tampilan modern + menuntun)."""
import streamlit as st

# 5 tahap alur kerja (untuk penunjuk langkah / stepper).
TAHAP = [
    ("Bersihkan", "pages/1_Pembersihan.py", "🧹"),
    ("Saring",    "pages/2_Penyaringan.py", "🔎"),
    ("Labeli",    "pages/3_Pelabelan.py",   "🏷️"),
    ("Latih",     "pages/4_Pelatihan.py",   "🤖"),
    ("Uji",       "pages/5_Prediksi_dan_Evaluasi.py", "📊"),
]

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --brand1:#6366F1; --brand2:#3B82F6; --ok:#10B981;
  --ink:#0F172A; --muted:#64748B; --line:#E2E8F0; --soft:#F1F5F9;
}
html, body, [class*="css"] { font-family:'Inter',sans-serif; }
[data-testid="stAppViewContainer"] { background:#F1F5F9; }
[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.4rem; padding-bottom:3rem; max-width:900px; }

/* ---- header gradient ---- */
.hero {
  background:linear-gradient(135deg,var(--brand1),var(--brand2));
  color:#fff; border-radius:18px; padding:22px 26px; margin-bottom:6px;
  box-shadow:0 10px 24px rgba(59,130,246,.25);
}
.hero h1 { font-size:22px; font-weight:700; margin:0; color:#fff; }
.hero p  { font-size:14px; margin:4px 0 0; color:#EAF0FF; opacity:.95; }

/* ---- stepper ---- */
.stepper { display:flex; align-items:flex-start; justify-content:space-between;
  margin:16px 2px 20px; }
.stp { display:flex; flex-direction:column; align-items:center; flex:1; position:relative; }
.stp .dot { width:38px; height:38px; border-radius:50%; display:flex;
  align-items:center; justify-content:center; font-weight:700; font-size:15px;
  background:#fff; color:var(--muted); border:2px solid var(--line); z-index:2; }
.stp .lbl { font-size:12px; margin-top:6px; color:var(--muted); font-weight:500; }
.stp.active .dot { background:linear-gradient(135deg,var(--brand1),var(--brand2));
  color:#fff; border-color:transparent; box-shadow:0 0 0 4px rgba(99,102,241,.18); }
.stp.active .lbl { color:var(--ink); font-weight:700; }
.stp.done .dot { background:var(--ok); color:#fff; border-color:transparent; }
.stp.done .lbl { color:var(--ink); }
.stp::after { content:""; position:absolute; top:19px; left:50%; width:100%;
  height:2px; background:var(--line); z-index:1; }
.stp:last-child::after { display:none; }
.stp.done::after { background:var(--ok); }

/* ---- kartu panduan ---- */
.panduan { background:#EFF4FF; border:1px solid #DCE6FF; border-left:4px solid var(--brand2);
  border-radius:12px; padding:14px 16px; margin:2px 0 16px; }
.panduan .j { font-weight:700; color:var(--ink); font-size:15px; margin-bottom:2px; }
.panduan .d { color:#475569; font-size:14px; line-height:1.5; }

/* ---- tombol ---- */
.stButton > button, .stDownloadButton > button {
  background:linear-gradient(135deg,var(--brand1),var(--brand2)); color:#fff;
  font-weight:600; border:none; border-radius:10px; padding:9px 22px;
  transition:transform .06s ease, box-shadow .2s ease; }
.stButton > button:hover, .stDownloadButton > button:hover {
  transform:translateY(-1px); box-shadow:0 6px 16px rgba(59,130,246,.3); color:#fff; }
.stButton > button:active { transform:translateY(0); }

/* ---- input ---- */
.stTextArea textarea, .stTextInput input {
  border-radius:10px; border:1px solid var(--line); background:#fff; font-size:15px; }
.stTextArea textarea:focus { border-color:var(--brand2);
  box-shadow:0 0 0 3px rgba(59,130,246,.15); }
[data-testid="stFileUploaderDropzone"] { border-radius:12px; border:1.5px dashed #C7D2FE;
  background:#FbFcFF; }

/* ---- metric jadi kartu ---- */
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line);
  border-radius:14px; padding:14px 16px; box-shadow:0 1px 2px rgba(15,23,42,.04); }

/* ---- kartu container ---- */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius:14px; }
div[data-testid="stExpander"] { border-radius:12px; border:1px solid var(--line); }

/* ---- radio jadi pill ---- */
div[role="radiogroup"] label { background:#fff; border:1px solid var(--line);
  border-radius:999px; padding:4px 12px; margin:2px 4px 2px 0; }

/* bar probabilitas */
.bar-row { display:flex; align-items:center; margin:7px 0; font-size:14px; color:#1e293b; }
.bar-name { width:110px; flex:none; font-weight:500; }
.bar-wrap { flex:1 1 auto; max-width:560px; background:#EEF2F7; border-radius:999px; }
.bar-fill { display:block; height:16px; border-radius:999px;
  background:linear-gradient(90deg,var(--brand1),var(--brand2)); min-width:6px; }
.bar-pct { margin-left:10px; min-width:44px; flex:none; color:#475569; font-weight:600; }

#MainMenu, footer {visibility:hidden;}
</style>
"""


def set_gaya(judul: str, subjudul: str = "", langkah: int = 0):
    """Pasang gaya global + hero header + (opsional) penunjuk tahap.
    langkah: 1..5 untuk menandai tahap aktif; 0 = tanpa stepper."""
    st.set_page_config(page_title="Deteksi Cyberbullying Discord",
                       page_icon="🛡️", layout="centered")
    st.markdown(_CSS, unsafe_allow_html=True)
    _gerbang()                       # gerbang kata sandi (aktif bila diset di secrets)
    sub = f"<p>{subjudul}</p>" if subjudul else ""
    st.markdown(f'<div class="hero"><h1>🛡️ {judul}</h1>{sub}</div>',
                unsafe_allow_html=True)
    if langkah:
        _stepper(langkah)


def _gerbang():
    """Gerbang kata sandi. Aktif HANYA bila [app].password diset di Secrets
    (mis. di Streamlit Cloud). Di lokal tanpa secrets -> otomatis terbuka."""
    try:
        sandi = st.secrets.get("app", {}).get("password")
    except Exception:
        sandi = None
    if not sandi or st.session_state.get("_auth_ok"):
        return
    st.markdown('<div class="hero" style="text-align:center"><h1>🛡️ Masuk</h1>'
                '<p>Aplikasi ini dilindungi kata sandi.</p></div>',
                unsafe_allow_html=True)
    s = st.text_input("Kata sandi", type="password")
    if st.button("Masuk"):
        if s == sandi:
            st.session_state["_auth_ok"] = True
            st.rerun()
        else:
            st.error("Kata sandi salah.")
    st.stop()


def _stepper(aktif: int):
    html = '<div class="stepper">'
    for i, (nama, _path, ikon) in enumerate(TAHAP, start=1):
        kelas = "done" if i < aktif else ("active" if i == aktif else "")
        isi = "✓" if i < aktif else str(i)
        html += (f'<div class="stp {kelas}"><div class="dot">{isi}</div>'
                 f'<div class="lbl">{ikon} {nama}</div></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def panduan(judul: str, isi: str):
    """Kotak penjelasan ramah: apa halaman ini & apa yang harus dilakukan."""
    st.markdown(f'<div class="panduan"><div class="j">💡 {judul}</div>'
                f'<div class="d">{isi}</div></div>', unsafe_allow_html=True)


def lanjut_ke(path: str, label: str):
    """Tombol/link menuju tahap berikutnya (menuntun alur)."""
    st.page_link(path, label=label, icon="➡️")


def bar_probabilitas(pasangan, ringkas: dict):
    html = ""
    for kelas, p in pasangan:
        nama = ringkas.get(kelas, kelas)
        html += (f'<div class="bar-row"><span class="bar-name">{nama}</span>'
                 f'<span class="bar-wrap"><span class="bar-fill" '
                 f'style="width:{p*100:.0f}%"></span></span>'
                 f'<span class="bar-pct">{p*100:.0f}%</span></div>')
    st.markdown(html, unsafe_allow_html=True)
