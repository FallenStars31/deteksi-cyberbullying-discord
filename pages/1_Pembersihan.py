# -*- coding: utf-8 -*-
"""Halaman 1 — Pengumpulan & Pembersihan Data (Tabel 3.1)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
from lib.ui import set_gaya, panduan, lanjut_ke
from lib import db
from lib.pembersihan import bersihkan

set_gaya("Bersihkan Data", "Langkah 1 dari 5", langkah=1)

panduan("Apa yang dilakukan di sini?",
        "Unggah file chat Discord Anda (format CSV, boleh beberapa sekaligus). "
        "Sistem otomatis membuang pesan bot, emoji, tautan, dan pesan kembar, "
        "lalu menyamarkan nama pengguna demi privasi. Hasilnya: daftar pesan bersih "
        "yang siap diproses di langkah berikutnya.")

n_ada = db.jumlah_baris("clean_messages")
if n_ada:
    st.info(f"Database sudah berisi **{n_ada:,}** pesan bersih. Membersihkan lagi "
            "akan **menggantinya**.")

berkas = st.file_uploader("Berkas CSV Discord (DiscordChatExporter)",
                          type="csv", accept_multiple_files=True)

if st.button("Bersihkan", type="primary"):
    if not berkas:
        st.warning("Unggah minimal satu berkas CSV dulu.")
        st.stop()
    frames = []
    for f in berkas:
        try:
            df = pd.read_csv(f, dtype=str, keep_default_na=False)
            frames.append((f.name, df))
        except Exception as e:
            st.error(f"Gagal membaca {f.name}: {e}")
    with st.spinner("Membersihkan..."):
        df_bersih, stat = bersihkan(frames)
    st.session_state["df_bersih"] = df_bersih
    st.session_state["stat_bersih"] = stat

if "stat_bersih" in st.session_state:
    stat = st.session_state["stat_bersih"]
    st.subheader("Tabel 3.1 — Hasil Pembersihan")
    tabel = pd.DataFrame({
        "Tahap": ["Pesan mentah (gabungan)", "Dibuang: bot/aplikasi",
                  "Dibuang: kosong", "Dibuang: hanya tautan/lampiran",
                  "Dibuang: hanya emoji", "Dibuang: duplikat",
                  "Pesan bersih (siap diproses)"],
        "Jumlah": [stat["mentah"], stat["bot"], stat["kosong"], stat["tautan"],
                   stat["emoji"], stat["duplikat"], stat["bersih"]],
    })
    st.dataframe(tabel, hide_index=True, use_container_width=True)
    st.caption("Sebaran per server: " +
               ", ".join(f"{k} {v:,}" for k, v in stat["sebaran_server"].items()))

    st.dataframe(st.session_state["df_bersih"].head(10), hide_index=True,
                 use_container_width=True)

    if st.button("💾 Simpan ke database", type="primary"):
        db.simpan_df("clean_messages", st.session_state["df_bersih"])
        st.success(f"Berhasil! {len(st.session_state['df_bersih']):,} pesan bersih tersimpan.")
        lanjut_ke("pages/2_Penyaringan.py", "Lanjut ke Langkah 2 · Saring pesan")
