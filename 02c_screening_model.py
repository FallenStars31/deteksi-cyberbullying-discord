# -*- coding: utf-8 -*-
"""
02c_screening_model.py
Penyaringan TAHAP 3 — dibantu MODEL (semi-otomatis / active learning).

Screening kata-kunci (02) & pola frasa (02b) melewatkan cyberbullying yang tak
memuat kata kasar eksplisit. Skrip ini menjalankan MODEL BINER terlatih ke
SELURUH pesan bersih yang BELUM dilabeli, lalu memunculkan pesan dengan
probabilitas cyberbullying tertinggi untuk ditinjau manual. Berguna menangkap
kasus yang lolos penyaringan lexicon.

Output: hasil/kandidat_model.csv  (kolom 'label' dikosongkan utk diisi manual)

Catatan: model berbasis kata (TF-IDF), jadi ia paling mampu menangkap kasus
dengan sinyal kata yang tak ada di lexicon (ejaan/varian/kata kontekstual);
sarkasme murni tanpa sinyal kata tetap sulit — dilaporkan jujur.
"""

import os
import re
import joblib
import pandas as pd
from importlib import import_module

m = import_module("03_nlp_naive_bayes")   # pakai praproses & kamus yg SAMA

FOLDER_OUT = "hasil"
AMBIL_TOP = 400          # jumlah kandidat teratas yang dimunculkan utk ditinjau
AMBANG_P = 0.60          # atau semua dgn P(cyberbullying) >= ambang ini

# --- praproses dgn cache stemmer (biar ~47rb pesan cepat) ---
_stem_cache = {}
def _stem(w):
    if w not in _stem_cache:
        _stem_cache[w] = m._stemmer.stem(w)
    return _stem_cache[w]

def praproses_cepat(teks: str) -> str:
    t = m.URL_RE.sub(" ", str(teks))
    t = re.sub(r"@\w+", " ", t)
    t = t.lower()
    t = m.NONALFA_RE.sub(" ", t)
    tok = m.TOKEN_RE.findall(t)
    tok = [m.KAMUS_NORM.get(w, w) for w in tok]
    tok = [w for w in tok if w not in m._stopword]
    tok = [_stem(w) for w in tok]
    return " ".join(tok)


def main():
    df = pd.read_csv(os.path.join(FOLDER_OUT, "data_bersih.csv"), keep_default_na=False)
    labeled = os.path.join(FOLDER_OUT, "dataset_berlabel.csv")
    sudah = (set(pd.read_csv(labeled, keep_default_na=False)["teks"].astype(str))
             if os.path.exists(labeled) else set())

    # hanya pesan yang BELUM dilabeli
    df = df[~df["teks"].astype(str).isin(sudah)].reset_index(drop=True)
    print(f"Pesan bersih belum berlabel: {len(df):,}")

    print("Praproses (stemmer ber-cache)...")
    df["clean"] = df["teks"].apply(praproses_cepat)
    df = df[df["clean"].str.strip() != ""].reset_index(drop=True)

    tfidf = joblib.load(os.path.join(FOLDER_OUT, "tfidf.joblib"))
    model_biner = joblib.load(os.path.join(FOLDER_OUT, "model_nb_biner.joblib"))
    model_6 = joblib.load(os.path.join(FOLDER_OUT, "model_nb.joblib"))

    X = tfidf.transform(df["clean"])
    i_bully = list(model_biner.classes_).index("cyberbullying")
    df["p_bully"] = model_biner.predict_proba(X)[:, i_bully].round(3)
    df["saran_kelas"] = model_6.predict(X)          # tebakan kategori (petunjuk)

    # tandai apakah ada kata kunci lexicon (utk lihat mana yg 'lolos' screening lama)
    kasar = set(pd.read_csv(os.path.join("kamus", "abusive.csv")).iloc[:, 0]
                .astype(str).str.lower())
    for b in {"anjir", "anjay", "wkwk"}:
        kasar.discard(b)
    df["ada_katakunci"] = df["clean"].apply(
        lambda c: "ya" if set(c.split()) & kasar else "tidak")

    # ranking: probabilitas cyberbullying tertinggi
    df = df.sort_values("p_bully", ascending=False).reset_index(drop=True)
    kandidat = df[df["p_bully"] >= AMBANG_P]
    if len(kandidat) < AMBIL_TOP:
        kandidat = df.head(AMBIL_TOP)
    kandidat = kandidat.copy()
    kandidat["label"] = ""

    # ringkasan
    tinggi = int((df["p_bully"] >= AMBANG_P).sum())
    lolos = int(((df["p_bully"] >= AMBANG_P) & (df["ada_katakunci"] == "tidak")).sum())
    print(f"\nPesan dgn P(cyberbullying) >= {AMBANG_P}: {tinggi:,}")
    print(f"  di antaranya TANPA kata kunci (lolos screening lama): {lolos:,}")
    print(f"Kandidat dimunculkan utk ditinjau: {len(kandidat):,}")

    cols = ["msg_id", "server", "teks", "p_bully", "saran_kelas", "ada_katakunci", "label"]
    cols = [c for c in cols if c in kandidat.columns]
    out = os.path.join(FOLDER_OUT, "kandidat_model.csv")
    kandidat[cols].to_csv(out, index=False, encoding="utf-8-sig")
    print(f"Disimpan -> {out}")
    print("Labeli kolom 'label' manual (boleh non_cyberbullying bila ternyata bukan).")


if __name__ == "__main__":
    main()
