# -*- coding: utf-8 -*-
"""Beranda.py — halaman utama = LAPORAN/dashboard (status data + hasil model).
Jalankan: streamlit run Beranda.py"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import streamlit as st
from lib.ui import set_gaya
from lib import db
from lib.labels import NAMA_TAMPIL

set_gaya("Deteksi Cyberbullying Discord", "Laporan sistem & hasil model")

# ============================ STATUS PEMROSESAN DATA ======================
n_bersih = db.jumlah_baris("clean_messages")
n_kandidat = db.jumlah_baris("candidates")
n_label = db.jumlah_baris("labeled_data")
ada_model = db.ada_artifact("model_biner.joblib")

st.subheader("Status pemrosesan data")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pesan siap disimpan", f"{n_bersih:,}")
c2.metric("Perlu dicek", f"{n_kandidat:,}")
c3.metric("Sudah dinilai", f"{n_label:,}")
c4.metric("Model", "Siap ✅" if ada_model else "Belum")

# ============================ DISTRIBUSI DATA BERLABEL ====================
lab = db.muat_df("labeled_data")
if not lab.empty and "label" in lab.columns:
    st.subheader("Distribusi data berlabel")
    dist = (lab["label"].value_counts()
            .rename(index=NAMA_TAMPIL).rename_axis("Kelas").reset_index(name="Jumlah"))
    dist["Persentase"] = (dist["Jumlah"] / dist["Jumlah"].sum() * 100).round(1).astype(str) + "%"
    st.dataframe(dist, hide_index=True, use_container_width=True)

# ============================ HASIL EVALUASI MODEL ========================
b = db.muat_artifact("metrik.json")
if b is None:
    st.info("Model belum dilatih. Buka halaman **Pelatihan** untuk melatih model.")
    st.stop()

metrik = json.loads(b.decode("utf-8"))


def tabel_metrik(laporan: dict) -> pd.DataFrame:
    baris = []
    for kelas, v in laporan.items():
        if isinstance(v, dict) and "precision" in v:
            baris.append({"Kelas": NAMA_TAMPIL.get(kelas, kelas),
                          "Precision": round(v["precision"], 3),
                          "Recall": round(v["recall"], 3),
                          "F1-score": round(v["f1-score"], 3),
                          "Data uji": int(v["support"])})
    return pd.DataFrame(baris)


st.subheader("Hasil evaluasi model")

# ---- Skema Enam Kelas ----
m = metrik["enam_kelas"]
st.markdown("#### Skema Enam Kelas")
k1, k2, k3 = st.columns(3)
k1.metric("Akurasi", f"{m['akurasi']:.3f}")
k2.metric("Macro-F1", f"{m['macro_f1']:.3f}")
k3.metric("Weighted-F1", f"{m['weighted_f1']:.3f}")
st.dataframe(tabel_metrik(m["laporan"]), hide_index=True, use_container_width=True)
cm6 = db.muat_artifact("cm_6kelas.png")
if cm6:
    st.image(cm6, caption="Confusion Matrix — Enam Kelas", use_container_width=True)

st.divider()

# ---- Skema Biner ----
m = metrik["biner"]
st.markdown("#### Skema Biner (cyberbullying vs non-cyberbullying)")
k1, k2, k3 = st.columns(3)
k1.metric("Akurasi", f"{m['akurasi']:.3f}")
k2.metric("Macro-F1", f"{m['macro_f1']:.3f}")
k3.metric("Baseline", f"{m.get('baseline', 0):.3f}")
st.dataframe(tabel_metrik(m["laporan"]), hide_index=True, use_container_width=True)
cm2 = db.muat_artifact("cm_biner.png")
if cm2:
    st.image(cm2, caption="Confusion Matrix — Biner", use_container_width=True)

# ---- Validasi silang ----
cv6, cv2 = metrik.get("cv_enam_kelas", {}), metrik.get("cv_biner", {})
if cv6 or cv2:
    st.divider()
    st.markdown("#### Validasi silang 5-lipat (rata-rata ± simpangan baku)")
    st.dataframe(pd.DataFrame([
        {"Skema": "Enam Kelas",
         "Akurasi": f"{cv6.get('akurasi_mean',0):.3f} ± {cv6.get('akurasi_std',0):.3f}",
         "Macro-F1": f"{cv6.get('macro_f1_mean',0):.3f} ± {cv6.get('macro_f1_std',0):.3f}"},
        {"Skema": "Biner",
         "Akurasi": f"{cv2.get('akurasi_mean',0):.3f} ± {cv2.get('akurasi_std',0):.3f}",
         "Macro-F1": f"{cv2.get('macro_f1_mean',0):.3f} ± {cv2.get('macro_f1_std',0):.3f}"},
    ]), hide_index=True, use_container_width=True)
