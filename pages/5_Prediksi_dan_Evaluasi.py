# -*- coding: utf-8 -*-
"""Halaman 5 — Prediksi pesan baru & Evaluasi model (confusion matrix + metrik)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
from lib.ui import set_gaya, panduan, lanjut_ke, bar_probabilitas
from lib import db
from lib.labels import RINGKAS, NAMA_TAMPIL
from lib.praproses import praproses

set_gaya("Coba & Lihat Hasil", "Langkah 5 dari 5", langkah=5)


@st.cache_resource
def muat_model():
    tfidf = db.muat_joblib("tfidf.joblib")
    m6 = db.muat_joblib("model_6.joblib")
    m2 = db.muat_joblib("model_biner.joblib")
    return tfidf, m6, m2


tfidf, model_6, model_biner = muat_model()
if tfidf is None or model_biner is None:
    st.warning("Sistem belum dilatih. Kerjakan **Langkah 4 · Latih** dulu.")
    lanjut_ke("pages/4_Pelatihan.py", "Ke Langkah 4 · Latih sistem")
    st.stop()

tab_deteksi, tab_eval = st.tabs(["🔍 Deteksi", "📊 Evaluasi Model"])

# ------------------------------------------------------------- TAB 1: DETEKSI
with tab_deteksi:
    skema = st.radio("Skema klasifikasi:", ["Enam Kelas", "Biner"], horizontal=True)
    teks = st.text_area("Masukkan teks pesan:", height=130,
                        placeholder="kamu bodoh banget, gausah ikut-ikut deh...")

    if st.button("Deteksi", type="primary") and teks.strip():
        model = model_6 if skema == "Enam Kelas" else model_biner
        bersih = praproses(teks)
        vek = tfidf.transform([bersih])
        pred = model.predict(vek)[0]
        proba = model.predict_proba(vek)[0]
        pasangan = sorted(zip(model.classes_, proba), key=lambda x: -x[1])

        warna = "#2E7D32" if pred == "non_cyberbullying" else "#CC0000"
        st.markdown(f"### Hasil: <span style='color:{warna}'>{NAMA_TAMPIL.get(pred, pred)}</span>",
                    unsafe_allow_html=True)
        bar_probabilitas(pasangan, RINGKAS)

# ------------------------------------------------------------- TAB 2: EVALUASI
with tab_eval:
    b = db.muat_artifact("metrik.json")
    if b is None:
        st.info("Metrik belum tersedia. Latih model di halaman Pelatihan.")
    else:
        metrik = json.loads(b.decode("utf-8"))

        def tabel(laporan):
            baris = []
            for kelas, v in laporan.items():
                if isinstance(v, dict) and "precision" in v:
                    baris.append({"Kelas": NAMA_TAMPIL.get(kelas, kelas),
                                  "Precision": round(v["precision"], 3),
                                  "Recall": round(v["recall"], 3),
                                  "F1-score": round(v["f1-score"], 3),
                                  "Data uji": int(v["support"])})
            return pd.DataFrame(baris)

        st.markdown("#### Skema Enam Kelas")
        m = metrik["enam_kelas"]
        st.markdown(f"Akurasi **{m['akurasi']:.3f}** · macro-F1 **{m['macro_f1']:.3f}** · "
                    f"weighted-F1 **{m['weighted_f1']:.3f}**")
        cm6 = db.muat_artifact("cm_6kelas.png")
        if cm6:
            st.image(cm6, caption="Confusion Matrix — Enam Kelas", use_container_width=True)
        st.dataframe(tabel(m["laporan"]), hide_index=True, use_container_width=True)

        st.divider()
        st.markdown("#### Skema Biner (cyberbullying vs non-cyberbullying)")
        m = metrik["biner"]
        st.markdown(f"Akurasi **{m['akurasi']:.3f}** · macro-F1 **{m['macro_f1']:.3f}** · "
                    f"baseline **{m.get('baseline', 0):.3f}**")
        cm2 = db.muat_artifact("cm_biner.png")
        if cm2:
            st.image(cm2, caption="Confusion Matrix — Biner", use_container_width=True)
        st.dataframe(tabel(m["laporan"]), hide_index=True, use_container_width=True)

        cv, cv6 = metrik.get("cv_biner", {}), metrik.get("cv_enam_kelas", {})
        if cv:
            st.caption(f"Validasi silang 5-lipat — 6 kelas: akurasi "
                       f"{cv6.get('akurasi_mean',0):.3f}±{cv6.get('akurasi_std',0):.3f} · "
                       f"biner: akurasi {cv.get('akurasi_mean',0):.3f}±{cv.get('akurasi_std',0):.3f}")
