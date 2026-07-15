# -*- coding: utf-8 -*-
"""Halaman 2 — Penyaringan kandidat cyberbullying (lexicon + pola + identitas + model)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
from lib.ui import set_gaya, panduan, lanjut_ke
from lib import db
from lib.penyaringan import saring, saring_model

set_gaya("Saring Pesan", "Langkah 2 dari 5", langkah=2)

n_bersih = db.jumlah_baris("clean_messages")
if not n_bersih:
    st.warning("Belum ada pesan bersih. Kerjakan **Langkah 1 · Bersihkan** dulu.")
    lanjut_ke("pages/1_Pembersihan.py", "Ke Langkah 1 · Bersihkan data")
    st.stop()

panduan("Apa yang dilakukan di sini?",
        f"Dari {n_bersih:,} pesan bersih, mustahil menilai satu per satu. Sistem "
        "menandai pesan yang <b>berpotensi</b> menyakiti (mengandung kata kasar, "
        "penyebutan identitas, atau pola ancaman/pengucilan) supaya Anda cukup menilai "
        "yang penting saja. Tekan tombol di bawah, lalu lanjut ke penilaian.")

# teks yang sudah dilabeli -> dikecualikan
lab = db.muat_df("labeled_data")
sudah = set(lab["teks"].astype(str)) if not lab.empty else set()

col1, col2 = st.columns(2)
with col1:
    if st.button("Jalankan penyaringan (A+B)", type="primary"):
        clean = db.muat_df("clean_messages")
        with st.spinner("Menyaring lexicon + pola + identitas..."):
            kand = saring(clean, sudah=sudah)
        db.simpan_df("candidates", kand)
        st.session_state["kand_ringkas"] = kand
        st.success(f"Ditemukan **{len(kand):,}** kandidat, tersimpan ke database.")

with col2:
    ada_model = db.ada_artifact("model_biner.joblib")
    if st.button("Cari lagi pakai model (C)", disabled=not ada_model):
        clean = db.muat_df("clean_messages")
        tfidf = db.muat_joblib("tfidf.joblib")
        m2 = db.muat_joblib("model_biner.joblib")
        m6 = db.muat_joblib("model_6.joblib")
        lama = db.muat_df("candidates")
        teks_lama = set(lama["teks"].astype(str)) if not lama.empty else set()
        with st.spinner("Active learning (model menyisir pesan)..."):
            kand_m = saring_model(clean, tfidf, m2, m6, sudah=sudah | teks_lama)
        if not kand_m.empty:
            db.simpan_df("candidates", kand_m, mode="append")
        st.session_state["kand_ringkas"] = db.muat_df("candidates")
        st.success(f"Tambahan **{len(kand_m):,}** kandidat dari model.")
    if not ada_model:
        st.caption("Model belum ada — latih dulu di halaman Pelatihan.")

# ringkasan kandidat
kand = st.session_state.get("kand_ringkas")
if kand is None:
    kand = db.muat_df("candidates")
if kand is not None and not kand.empty:
    st.divider()
    st.subheader(f"Ringkasan kandidat ({len(kand):,})")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Per saran kelas")
        st.dataframe(kand["saran_kelas"].value_counts().rename_axis("saran_kelas")
                     .reset_index(name="jumlah"), hide_index=True, use_container_width=True)
    with c2:
        st.caption("Per strategi")
        strat = kand["strategi"].str.split(";").explode().value_counts()
        st.dataframe(strat.rename_axis("strategi").reset_index(name="jumlah"),
                     hide_index=True, use_container_width=True)
    lanjut_ke("pages/3_Pelabelan.py", "Lanjut ke Langkah 3 · Nilai pesan")
