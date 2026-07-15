# -*- coding: utf-8 -*-
"""Halaman 3 — Pelabelan semi-otomatis. Sistem MENYARANKAN, Anda MEMUTUSKAN."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
from lib.ui import set_gaya, panduan, lanjut_ke
from lib import db
from lib.labels import KELAS, NAMA_TAMPIL

set_gaya("Nilai Pesan", "Langkah 3 dari 5", langkah=3)

kand = db.muat_df("candidates")
if kand.empty:
    st.warning("Belum ada pesan untuk dinilai. Kerjakan **Langkah 2 · Saring** dulu.")
    lanjut_ke("pages/2_Penyaringan.py", "Ke Langkah 2 · Saring pesan")
    st.stop()

lab = db.muat_df("labeled_data")
sudah_teks = set(lab["teks"].astype(str)) if not lab.empty else set()
st.session_state.setdefault("lewati", set())

# kolam kandidat yang belum dilabeli & belum dilewati sesi ini
belum = kand[~kand["teks"].astype(str).isin(sudah_teks)
             & ~kand["teks"].astype(str).isin(st.session_state["lewati"])]

total = len(kand)
selesai = len(set(kand["teks"].astype(str)) & sudah_teks)
st.progress(selesai / total if total else 0.0,
            text=f"Sudah dilabeli {selesai:,} dari {total:,} kandidat")

panduan("Bagaimana cara menilai?",
        "Baca pesannya, lalu pilih jenisnya. <b>Sistem sudah memberi saran</b> — bila "
        "setuju, langsung <i>Simpan</i>. Ingat: adanya kata kasar belum tentu "
        "cyberbullying — yang penting <b>apakah pesan itu menyerang seseorang</b>. "
        "Kalau ragu atau cuma umpatan tanpa sasaran, pilih <i>Non-Cyberbullying</i>.")

with st.expander("📖 Arti tiap jenis (klik bila ragu)"):
    st.markdown("""
- **Penghinaan** — menghina/mencela seseorang ("dasar bodoh, gak guna").
- **Ancaman** — mengancam menyakiti ("awas, gua samperin ke rumah").
- **Ujaran Kebencian** — menyerang suku/agama/ras/gender ("orang X gak pantes di sini").
- **Pelecehan** — mengganggu seseorang terus-menerus.
- **Pengucilan** — mengeluarkan seseorang dari kelompok ("jangan diajak dia").
- **Non-Cyberbullying** — obrolan biasa, candaan, umpatan tanpa sasaran manusia.

*Bila kena beberapa jenis:* ancaman > ujaran kebencian > pelecehan > pengucilan > penghinaan.
""")

if belum.empty:
    st.success("🎉 Semua pesan sudah dinilai. Sistem siap dilatih!")
    lanjut_ke("pages/4_Pelatihan.py", "Lanjut ke Langkah 4 · Latih sistem")
    if st.session_state["lewati"]:
        if st.button("Nilai lagi yang tadi dilewati"):
            st.session_state["lewati"] = set()
            st.rerun()
    st.stop()

# ---- kandidat saat ini ----
kar = belum.iloc[0]
teks = str(kar["teks"])
saran = str(kar.get("saran_kelas", "")) if str(kar.get("saran_kelas", "")) in KELAS else "non_cyberbullying"
strategi = str(kar.get("strategi", ""))
kata = str(kar.get("kata_terdeteksi", "") or "")
pb = kar.get("p_bully", None)

st.divider()
st.markdown(f"#### Pesan")
st.markdown(f"> {teks}")
info = f"**Saran sistem:** `{saran}`"
if strategi:
    info += f"  ·  strategi: `{strategi}`"
if kata:
    info += f"  ·  kata terdeteksi: `{kata}`"
if pb not in (None, "") and not pd.isna(pb):
    info += f"  ·  P(bully): `{pb}`"
st.caption(info)

pilihan = st.radio("Label final:", KELAS,
                   index=KELAS.index(saran),
                   format_func=lambda k: NAMA_TAMPIL.get(k, k), horizontal=True)

c1, c2, _ = st.columns([1, 1, 2])
with c1:
    if st.button("💾 Simpan & lanjut", type="primary"):
        baris = pd.DataFrame([{
            "msg_id": kar.get("msg_id", ""),
            "server": kar.get("server", ""),
            "author_anon": kar.get("author_anon", ""),
            "teks": teks,
            "label": pilihan,
            "sumber": "pelabelan_web",
        }])
        db.simpan_df("labeled_data", baris, mode="append")
        st.rerun()
with c2:
    if st.button("⏭️ Lewati"):
        st.session_state["lewati"].add(teks)
        st.rerun()
