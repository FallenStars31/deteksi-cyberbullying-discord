# -*- coding: utf-8 -*-
"""Halaman 4 — Pelatihan & evaluasi model Naïve Bayes."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
from lib.ui import set_gaya, panduan, lanjut_ke
from lib import db
from lib.labels import KELAS, NAMA_TAMPIL
from lib.pemodelan import latih

set_gaya("Latih Sistem", "Langkah 4 dari 5", langkah=4)

lab = db.muat_df("labeled_data")
if lab.empty:
    st.warning("Belum ada pesan yang dinilai. Kerjakan **Langkah 3 · Nilai** dulu.")
    lanjut_ke("pages/3_Pelabelan.py", "Ke Langkah 3 · Nilai pesan")
    st.stop()

lab = lab[lab["label"].isin(KELAS)]
panduan("Apa yang dilakukan di sini?",
        f"Sistem belajar dari <b>{len(lab):,} pesan</b> yang sudah Anda nilai, supaya "
        "kelak bisa menebak sendiri pesan baru. Cukup tekan tombol dan tunggu "
        "sebentar (1–2 menit). Setelah selesai, akurasinya langsung ditampilkan.")

dist = lab["label"].value_counts().rename(index=NAMA_TAMPIL)
st.dataframe(dist.rename_axis("Kelas").reset_index(name="Jumlah"),
             hide_index=True, use_container_width=True)

if lab["label"].nunique() < 2:
    st.error("Perlu minimal 2 kelas untuk melatih.")
    st.stop()

if st.button("🤖 Latih model sekarang", type="primary"):
    kotak = st.empty()
    prog = st.progress(0.0)
    langkah = {"n": 0}

    def lapor(msg):
        langkah["n"] = min(langkah["n"] + 1, 6)
        kotak.write(f"⏳ {msg}")
        prog.progress(langkah["n"] / 6.0)

    with st.spinner("Melatih... (mungkin 1–2 menit)"):
        hasil = latih(lab[["teks", "label"]], lapor=lapor)
        db.simpan_joblib("model_6.joblib", hasil["model_6"])
        db.simpan_joblib("model_biner.joblib", hasil["model_biner"])
        db.simpan_joblib("tfidf.joblib", hasil["tfidf"])
        db.simpan_artifact("metrik.json",
                           json.dumps(hasil["metrik"], ensure_ascii=False).encode("utf-8"))
        db.simpan_artifact("cm_6kelas.png", hasil["cm6_png"])
        db.simpan_artifact("cm_biner.png", hasil["cm2_png"])
    prog.progress(1.0)
    st.cache_resource.clear()  # agar halaman Prediksi memuat model baru
    st.session_state["metrik_baru"] = hasil["metrik"]
    st.success("Selesai! Sistem sudah pintar dan siap dicoba.")
    lanjut_ke("pages/5_Prediksi_dan_Evaluasi.py", "Lanjut ke Langkah 5 · Coba & lihat hasil")

m = st.session_state.get("metrik_baru")
if m:
    st.divider()
    st.subheader("Hasil")
    e, b = m["enam_kelas"], m["biner"]
    c1, c2 = st.columns(2)
    c1.metric("6 kelas — Akurasi", f"{e['akurasi']:.3f}", f"macro-F1 {e['macro_f1']:.3f}")
    c2.metric("Biner — Akurasi", f"{b['akurasi']:.3f}", f"macro-F1 {b['macro_f1']:.3f}")
    st.caption(f"Validasi silang 5-lipat — 6 kelas "
               f"{m['cv_enam_kelas']['akurasi_mean']:.3f}±{m['cv_enam_kelas']['akurasi_std']:.3f} · "
               f"biner {m['cv_biner']['akurasi_mean']:.3f}±{m['cv_biner']['akurasi_std']:.3f}. "
               "Lihat confusion matrix di halaman **📊 Prediksi & Evaluasi**.")
