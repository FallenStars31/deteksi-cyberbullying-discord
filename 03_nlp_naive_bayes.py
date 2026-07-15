# -*- coding: utf-8 -*-
"""
03_nlp_naive_bayes.py
Pipeline NLP + Multinomial Naive Bayes (sesuai BAB III & BAB V skripsi).

Urutan praproses (PERSIS BAB III - Analisa Proses):
  1. Cleaning      : hapus mention, emoji, tautan, tanda baca, karakter non-alfabet
  2. Case Folding  : huruf kecil
  3. Tokenisasi    : pecah jadi token
  4. Normalisasi   : slang -> baku (kamus normalisasi)
  5. Stopword Removal (stopword bahasa Indonesia)
  6. Stemming      : Sastrawi
  7. TF-IDF        : TfidfVectorizer

Model      : MultinomialNB (Multinomial Naive Bayes)
Tuning     : alpha (Laplace smoothing) via k-fold cross-validation

PENTING (tanpa oversampling / resampling):
  Kedua skenario dilatih TANPA oversampling. Uji ablasi (validasi silang
  5-lipat, konfigurasi lain identik) menunjukkan oversampling justru
  MERUSAK model enam-kelas: menggandakan dokumen minoritas mendistorsi
  prior & likelihood Naive Bayes sehingga model kelewat agresif menandai
  kelas minoritas (banjir false positive). TF-IDF dijalankan DI DALAM
  pipeline agar hanya di-fit pada lipatan latih saat cross-validation
  (mencegah kebocoran data / data leakage).

Dua skenario pengujian (sesuai BAB V):
  A. Enam kelas   : TANPA oversampling (oversampling menurunkan macro-F1)
  B. Biner        : cyberbullying vs non_cyberbullying, TANPA resampling
                    (rasio lebih ringan; resampling justru menurunkan presisi)

Evaluasi : split 80:20 stratified; accuracy, precision, recall, F1
           (per-kelas + macro/weighted) dan confusion matrix.
"""

import os
import re
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import (train_test_split, GridSearchCV,
                                     StratifiedKFold, cross_validate)
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score, f1_score, ConfusionMatrixDisplay)

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from sklearn.pipeline import Pipeline   # TF-IDF di dalam pipeline (anti-kebocoran)

FOLDER_OUT   = "hasil"
FOLDER_KAMUS = "kamus"
SEED         = 42
KELAS = ["insult", "threat", "hate_speech", "harassment", "exclusion", "non_cyberbullying"]

# ---- alat praproses --------------------------------------------------------
_stemmer  = StemmerFactory().create_stemmer()
_stopword = set(StopWordRemoverFactory().get_stop_words())
URL_RE     = re.compile(r"https?://\S+|www\.\S+")
NONALFA_RE = re.compile(r"[^a-z\s]")          # sisakan huruf saja (buang emoji/angka/tanda baca)
TOKEN_RE   = re.compile(r"[a-z]+")


def muat_kamus_normalisasi() -> dict:
    path = os.path.join(FOLDER_KAMUS, "colloquial-indonesian-lexicon.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        kol = {c.lower(): c for c in df.columns}
        s = kol.get("slang")
        f = kol.get("formal") or kol.get("baku")
        if s and f:
            return dict(zip(df[s].astype(str), df[f].astype(str)))
    return {"gw": "saya", "gue": "saya", "lo": "kamu", "lu": "kamu", "bgt": "banget",
            "gk": "tidak", "ga": "tidak", "yg": "yang", "udh": "sudah", "aja": "saja"}


KAMUS_NORM = muat_kamus_normalisasi()


def praproses(teks: str) -> str:
    """Tujuh tahap praproses sesuai BAB III (Analisa Proses)."""
    t = str(teks)
    t = URL_RE.sub(" ", t)                          # (1) cleaning: tautan
    t = re.sub(r"@\w+", " ", t)                     # (1) cleaning: mention
    t = t.lower()                                   # (2) case folding
    t = NONALFA_RE.sub(" ", t)                      # (1) cleaning: emoji/tanda baca/angka
    tok = TOKEN_RE.findall(t)                       # (3) tokenisasi
    tok = [KAMUS_NORM.get(w, w) for w in tok]       # (4) normalisasi slang -> baku
    tok = [w for w in tok if w not in _stopword]    # (5) stopword removal
    tok = [_stemmer.stem(w) for w in tok]           # (6) stemming (Sastrawi)
    return " ".join(tok)


def simpan_cm(yte, ypred, labels, judul, nama_file):
    cm = confusion_matrix(yte, ypred, labels=labels)
    fig, ax = plt.subplots(figsize=(7, 6) if len(labels) > 2 else (4.5, 4))
    ConfusionMatrixDisplay(cm, display_labels=labels).plot(
        ax=ax, cmap="Blues", xticks_rotation=45, colorbar=False, values_format="d")
    ax.set_title(judul)
    fig.tight_layout()
    fig.savefig(os.path.join(FOLDER_OUT, nama_file), dpi=200)
    plt.close(fig)
    print(f"Confusion matrix disimpan -> {os.path.join(FOLDER_OUT, nama_file)}")


def evaluasi(nama, X_text, y):
    """Latih + uji satu skenario. TANPA oversampling; TF-IDF di DALAM pipeline
    sehingga hanya di-fit pada lipatan latih (tidak bocor saat cross-validation)."""
    Xtr, Xte, ytr, yte = train_test_split(
        X_text, y, test_size=0.20, stratify=y, random_state=SEED)

    pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2)),
                     ("nb", MultinomialNB())])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    grid = GridSearchCV(
        pipe, param_grid={"nb__alpha": [0.01, 0.05, 0.1, 0.5, 1.0]},
        scoring="f1_macro", cv=cv, n_jobs=-1)
    grid.fit(Xtr, ytr)
    model = grid.best_estimator_
    ypred = model.predict(Xte)

    labels = [k for k in (KELAS if len(set(y)) > 2 else ["cyberbullying", "non_cyberbullying"])
              if k in set(yte)]
    print("\n" + "=" * 60)
    print(f"SKENARIO: {nama}  (tanpa oversampling)")
    print("=" * 60)
    print(f"Alpha terbaik (CV, valid): {grid.best_params_['nb__alpha']} "
          f"| f1_macro CV: {grid.best_score_:.4f}")
    print(f"Akurasi (data uji)  : {accuracy_score(yte, ypred):.4f}")
    print(f"macro-F1 (data uji) : {f1_score(yte, ypred, average='macro', zero_division=0):.4f}")
    print(f"weighted-F1         : {f1_score(yte, ypred, average='weighted', zero_division=0):.4f}")
    print("\nLaporan klasifikasi (precision/recall/F1 per kelas):")
    print(classification_report(yte, ypred, labels=labels, digits=4, zero_division=0))
    return model, yte, ypred, labels


def main():
    # ---- muat data berlabel (hasil verifikasi manusia = ground truth) -----
    path = os.path.join(FOLDER_OUT, "dataset_berlabel.csv")
    df = pd.read_csv(path)
    df = df[df["label"].isin(KELAS)].dropna(subset=["teks"]).reset_index(drop=True)
    print(f"Total data berlabel: {len(df)}")
    print("Distribusi kelas:\n", df["label"].value_counts().to_string(), "\n")

    print("Memproses teks (praproses 1-6)...")
    df["clean"] = df["teks"].apply(praproses)
    df = df[df["clean"].str.strip() != ""].reset_index(drop=True)
    X_text = df["clean"]

    # ---------- A. ENAM KELAS (TANPA oversampling) ----------
    model6, yte6, yp6, lab6 = evaluasi("Enam kelas", X_text, df["label"])
    simpan_cm(yte6, yp6, lab6, "Confusion Matrix - Naive Bayes (6 Kelas)",
              "confusion_matrix_6kelas.png")

    # ---------- B. BINER (tanpa resampling) ----------
    y_biner = df["label"].map(
        lambda k: "non_cyberbullying" if k == "non_cyberbullying" else "cyberbullying")
    model2, yte2, yp2, lab2 = evaluasi("Biner (cyberbullying vs non)", X_text, y_biner)
    base = (yte2 == "non_cyberbullying").mean()
    print(f"Baseline 'selalu prediksi normal': {base:.4f}")
    simpan_cm(yte2, yp2, ["cyberbullying", "non_cyberbullying"],
              "Confusion Matrix - Naive Bayes (Biner)", "confusion_matrix_biner.png")

    # ---------- C. VALIDASI SILANG 5-LIPAT (estimasi lebih stabil) ----------
    #   Seluruh data bergiliran jadi data uji -> cocok untuk data timpang/kecil,
    #   tak mengorbankan data latih seperti split tunggal.
    def validasi_silang(nama, y, alpha):
        pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2)),
                         ("nb", MultinomialNB(alpha=alpha))])
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        r = cross_validate(pipe, X_text, y, cv=cv, scoring=["accuracy", "f1_macro"])
        a, f = r["test_accuracy"], r["test_f1_macro"]
        print(f"  {nama:12s}: akurasi {a.mean():.4f} ± {a.std():.4f} | "
              f"macro-F1 {f.mean():.4f} ± {f.std():.4f}")
        return {"akurasi_mean": float(a.mean()), "akurasi_std": float(a.std()),
                "macro_f1_mean": float(f.mean()), "macro_f1_std": float(f.std())}

    print("\n" + "=" * 60)
    print("VALIDASI SILANG 5-LIPAT (rata-rata +/- simpangan baku)")
    print("=" * 60)
    # alpha = 0.01 untuk kedua skema (nilai terbaik hasil GridSearchCV di atas)
    cv6 = validasi_silang("Enam kelas", df["label"], 0.01)
    cv2 = validasi_silang("Biner", y_biner, 0.01)

    # ---- simpan metrik ke JSON agar dapat ditampilkan di antarmuka ---------
    def _rangkum(yte, yp, labels):
        return {
            "akurasi": float(accuracy_score(yte, yp)),
            "macro_f1": float(f1_score(yte, yp, average="macro", zero_division=0)),
            "weighted_f1": float(f1_score(yte, yp, average="weighted", zero_division=0)),
            "laporan": classification_report(yte, yp, labels=labels,
                                             output_dict=True, zero_division=0),
        }
    metrik = {
        "enam_kelas": _rangkum(yte6, yp6, lab6),
        "biner": _rangkum(yte2, yp2, ["cyberbullying", "non_cyberbullying"]),
    }
    metrik["biner"]["baseline"] = float(base)
    metrik["cv_enam_kelas"] = cv6
    metrik["cv_biner"] = cv2
    with open(os.path.join(FOLDER_OUT, "metrik.json"), "w", encoding="utf-8") as f:
        json.dump(metrik, f, indent=2, ensure_ascii=False)
    print(f"Metrik disimpan -> {os.path.join(FOLDER_OUT, 'metrik.json')}")

    # ---- latih ulang pd SELURUH data + simpan model utk antarmuka --------
    #      Dua skema sesuai naskah: (a) ENAM KELAS untuk tampilan probabilitas
    #      tiap kategori, dan (b) BINER (cyberbullying vs non) sebagai hasil
    #      utama. Keduanya berbagi TF-IDF yang sama.
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
    Xall = tfidf.fit_transform(X_text)

    # alpha = 0.01 untuk kedua skema (konsisten dgn GridSearchCV & validasi silang)
    model_6kelas = MultinomialNB(alpha=0.01).fit(Xall, df["label"])
    y_biner_all = df["label"].map(
        lambda k: "non_cyberbullying" if k == "non_cyberbullying" else "cyberbullying")
    model_biner = MultinomialNB(alpha=0.01).fit(Xall, y_biner_all)

    joblib.dump(model_6kelas, os.path.join(FOLDER_OUT, "model_nb.joblib"))
    joblib.dump(model_biner, os.path.join(FOLDER_OUT, "model_nb_biner.joblib"))
    joblib.dump(tfidf, os.path.join(FOLDER_OUT, "tfidf.joblib"))
    print("\nModel & vectorizer disimpan "
          "(model_nb.joblib, model_nb_biner.joblib, tfidf.joblib).")
    print("Selesai. Salin metrik & confusion matrix di atas ke BAB V.")


if __name__ == "__main__":
    main()
