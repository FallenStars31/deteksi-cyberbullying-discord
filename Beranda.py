# -*- coding: utf-8 -*-
"""Beranda.py — halaman utama (sambutan + status). Jalankan: streamlit run Beranda.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from lib.ui import set_gaya, panduan
from lib import db

set_gaya("Deteksi Cyberbullying Discord",
         "Kenali pesan yang menyakiti di chat Discord — otomatis, berbahasa Indonesia.")

panduan("Selamat datang! 👋",
        "Aplikasi ini membantu Anda membangun sistem pendeteksi <i>cyberbullying</i> "
        "dari nol, cukup lewat halaman web ini — tanpa perlu paham kode. "
        "Ikuti <b>5 langkah</b> di bawah secara berurutan. Bila baru pertama kali, "
        "mulai dari langkah 1.")

# ---- status ringkas ----
n_bersih = db.jumlah_baris("clean_messages")
n_kandidat = db.jumlah_baris("candidates")
n_label = db.jumlah_baris("labeled_data")
ada_model = db.ada_artifact("model_biner.joblib")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pesan siap", f"{n_bersih:,}")
c2.metric("Perlu dicek", f"{n_kandidat:,}")
c3.metric("Sudah dinilai", f"{n_label:,}")
c4.metric("Model", "Siap ✅" if ada_model else "Belum")

st.write("")
st.subheader("Langkah pengerjaan")

LANGKAH = [
    ("1", "🧹", "Bersihkan data", "Unggah file chat Discord, sistem merapikannya otomatis.",
     "pages/1_Pembersihan.py"),
    ("2", "🔎", "Saring pesan", "Sistem menandai pesan yang berpotensi menyakiti.",
     "pages/2_Penyaringan.py"),
    ("3", "🏷️", "Nilai pesan", "Anda menilai: pesan ini termasuk jenis apa? (sistem memberi saran).",
     "pages/3_Pelabelan.py"),
    ("4", "🤖", "Latih sistem", "Sistem belajar dari penilaian Anda. Cukup satu klik.",
     "pages/4_Pelatihan.py"),
    ("5", "📊", "Coba & lihat hasil", "Uji pesan baru dan lihat seberapa akurat sistemnya.",
     "pages/5_Prediksi_dan_Evaluasi.py"),
]
for no, ikon, judul, ket, path in LANGKAH:
    with st.container(border=True):
        k1, k2 = st.columns([5, 2])
        with k1:
            st.markdown(f"**{ikon} Langkah {no} — {judul}**")
            st.caption(ket)
        with k2:
            st.page_link(path, label="Buka", icon="➡️")

st.caption(f"Penyimpanan: {'lokal (SQLite)' if db.is_sqlite() else 'online (Supabase)'} · "
           "6 jenis label: penghinaan, ancaman, ujaran kebencian, pelecehan, pengucilan, non-cyberbullying.")
