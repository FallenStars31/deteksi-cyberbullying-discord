# -*- coding: utf-8 -*-
"""
04_antarmuka_streamlit.py
Antarmuka web (BAB IV - Perancangan Interface, Gambar 4.10 & BAB V -
Implementasi & Pengujian). Dua tab:
  • Deteksi        : prediksi satu pesan (dua skema: Enam Kelas & Biner),
                     tampilan mengikuti rancangan Gambar 4.10.
  • Evaluasi Model : confusion matrix (Gambar 5.1 & 5.2) + tabel metrik
                     per kelas, dibaca dari hasil/metrik.json.

Jalankan:  streamlit run 04_antarmuka_streamlit.py
(perlu model_nb.joblib, model_nb_biner.joblib, tfidf.joblib, metrik.json,
 dan kedua confusion_matrix_*.png hasil 03_nlp_naive_bayes.py)
"""

import os
import json
import joblib
import pandas as pd
import streamlit as st
from importlib import import_module

# pakai fungsi praproses yang SAMA dengan tahap pelatihan (urutan 1-6 identik)
praproses = import_module("03_nlp_naive_bayes").praproses

FOLDER_OUT = "hasil"

# singkatan nama kelas untuk label bar (sesuai Gambar 4.10)
KELAS_SINGKAT = {
    "insult": "insult", "non_cyberbullying": "non_cb", "harassment": "harass",
    "threat": "threat", "exclusion": "excl", "hate_speech": "hate",
    "cyberbullying": "bully",
}

st.set_page_config(page_title="Deteksi Cyberbullying Discord",
                   page_icon="🛡️", layout="centered")

# ---------------------------------------------------------------- gaya (CSS)
st.markdown("""
<style>
#MainMenu, header, footer {visibility: hidden;}
.block-container {padding-top: 1.6rem; max-width: 860px;}

.app-header {
    background:#3B6FD4; color:#FFFFFF; font-weight:700; font-size:27px;
    text-align:center; padding:20px 16px; border-radius:4px; margin-bottom:16px;
}
.input-label {font-size:19px; color:#111; margin:2px 0 4px 2px;}
div[role="radiogroup"] {gap:22px;}
.stRadio label p {font-size:16px; color:#111;}
.stTabs [data-baseweb="tab"] {font-size:16px; font-weight:600;}

.stTextArea textarea {
    background:#F7F9FC; border:1px solid #AAAAAA !important; border-radius:4px;
    font-size:16px; color:#111; min-height:150px;
}
.stTextArea textarea::placeholder {color:#9AA0A6;}

.stButton > button {
    background:#3B6FD4; color:#FFFFFF; font-weight:700; font-size:17px;
    border:none; border-radius:4px; padding:9px 40px; margin-top:6px;
}
.stButton > button:hover {background:#3160BC; color:#FFFFFF;}
.stButton > button:active, .stButton > button:focus {
    background:#3160BC !important; color:#FFFFFF !important; box-shadow:none !important;
}

.result-box {
    background:#EEF7EE; border:1px solid #8BC18B; border-radius:4px;
    padding:18px 22px; margin-top:22px;
}
.hasil-line {font-size:20px; margin-bottom:14px; color:#111;}
.hasil-key {font-weight:700;}
.bar-row {display:flex; align-items:center; margin:8px 0; font-size:15px; color:#222;}
.bar-name {width:92px; flex:none;}
.bar-wrap {flex:1 1 auto; max-width:640px; display:block;}
.bar-fill {display:block; height:20px; background:#3B6FD4; border-radius:2px; min-width:2px;}
.bar-pct {margin-left:10px; min-width:46px; flex:none;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------- header
st.markdown('<div class="app-header">Deteksi Cyberbullying Discord</div>',
            unsafe_allow_html=True)


@st.cache_resource
def muat_model():
    tfidf = joblib.load(os.path.join(FOLDER_OUT, "tfidf.joblib"))
    model_6kelas = joblib.load(os.path.join(FOLDER_OUT, "model_nb.joblib"))
    model_biner = joblib.load(os.path.join(FOLDER_OUT, "model_nb_biner.joblib"))
    return tfidf, model_6kelas, model_biner


@st.cache_data
def muat_metrik():
    p = os.path.join(FOLDER_OUT, "metrik.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def tabel_metrik(laporan: dict) -> pd.DataFrame:
    """Ubah classification_report (dict) -> DataFrame precision/recall/F1/support."""
    baris = []
    for kelas, v in laporan.items():
        if isinstance(v, dict):
            baris.append({
                "Kelas": kelas,
                "Precision": round(v["precision"], 3),
                "Recall": round(v["recall"], 3),
                "F1-score": round(v["f1-score"], 3),
                "Data uji": int(v["support"]),
            })
    return pd.DataFrame(baris)


try:
    tfidf, model_6kelas, model_biner = muat_model()
except Exception:
    st.error("Model belum ada. Jalankan 03_nlp_naive_bayes.py terlebih dahulu.")
    st.stop()

metrik = muat_metrik()

tab_deteksi, tab_eval = st.tabs(["🔍  Deteksi", "📊  Evaluasi Model"])

# ============================ TAB 1: DETEKSI (Gambar 4.10) =================
with tab_deteksi:
    skema = st.radio("Skema klasifikasi:", ["Enam Kelas", "Biner"], horizontal=True)

    st.markdown('<p class="input-label">Masukkan teks pesan:</p>', unsafe_allow_html=True)
    teks = st.text_area("Masukkan teks pesan", height=150,
                        placeholder="kamu bodoh banget...",
                        label_visibility="collapsed")

    if st.button("Deteksi", type="primary") and teks.strip():
        model = model_6kelas if skema == "Enam Kelas" else model_biner
        bersih = praproses(teks)
        vek = tfidf.transform([bersih])
        pred = model.predict(vek)[0]
        proba = model.predict_proba(vek)[0]

        pasangan = sorted(zip(model.classes_, proba), key=lambda x: -x[1])
        baris = ""
        for kelas, p in pasangan:
            nama = KELAS_SINGKAT.get(kelas, kelas)
            baris += (
                f'<div class="bar-row"><span class="bar-name">{nama}</span>'
                f'<span class="bar-wrap"><span class="bar-fill" style="width:{p*100:.0f}%"></span></span>'
                f'<span class="bar-pct">{p*100:.0f}%</span></div>'
            )

        warna = "#2E7D32" if pred == "non_cyberbullying" else "#CC0000"
        st.markdown(
            f'<div class="result-box">'
            f'<div class="hasil-line"><span class="hasil-key">Hasil:</span> '
            f'<span style="color:{warna}; font-weight:700;">{pred.upper()}</span></div>'
            f'{baris}</div>',
            unsafe_allow_html=True,
        )

# ============================ TAB 2: EVALUASI MODEL ========================
with tab_eval:
    cm6 = os.path.join(FOLDER_OUT, "confusion_matrix_6kelas.png")
    cm2 = os.path.join(FOLDER_OUT, "confusion_matrix_biner.png")

    if metrik is None:
        st.info("Metrik belum tersedia. Jalankan `03_nlp_naive_bayes.py` "
                "untuk menghasilkan confusion matrix & metrik.")
    else:
        st.markdown("#### Skema Enam Kelas")
        m = metrik["enam_kelas"]
        st.markdown(f"Akurasi **{m['akurasi']:.3f}**  ·  macro-F1 **{m['macro_f1']:.3f}**  "
                    f"·  weighted-F1 **{m['weighted_f1']:.3f}**")
        if os.path.exists(cm6):
            st.image(cm6, caption="Gambar 5.1  Confusion Matrix Klasifikasi Enam Kelas",
                     use_container_width=True)
        st.dataframe(tabel_metrik(m["laporan"]), hide_index=True, use_container_width=True)

        st.divider()

        st.markdown("#### Skema Biner (cyberbullying vs non-cyberbullying)")
        m = metrik["biner"]
        st.markdown(f"Akurasi **{m['akurasi']:.3f}**  ·  macro-F1 **{m['macro_f1']:.3f}**  "
                    f"·  baseline **{m.get('baseline', 0):.3f}**")
        if os.path.exists(cm2):
            st.image(cm2, caption="Gambar 5.2  Confusion Matrix Klasifikasi Biner",
                     use_container_width=True)
        st.dataframe(tabel_metrik(m["laporan"]), hide_index=True, use_container_width=True)
