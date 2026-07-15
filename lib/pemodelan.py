# -*- coding: utf-8 -*-
"""
lib/pemodelan.py
Pelatihan & evaluasi Multinomial Naive Bayes (dipisah dari 03_nlp_naive_bayes.py).
Logika IDENTIK naskah BAB V:
  - praproses 7 tahap -> TF-IDF (n-gram 1-2, min_df=2) DI DALAM Pipeline (anti-bocor)
  - tuning alpha via GridSearchCV (f1_macro, StratifiedKFold 5)
  - split 80:20 stratified + validasi silang 5-lipat
  - dua skema: enam kelas & biner (cyberbullying vs non), TANPA oversampling
  - keluaran: metrik dict + confusion matrix (PNG bytes) + model + tfidf

Fungsi:
  latih(df_berlabel, lapor=None) -> dict
"""

import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import (train_test_split, GridSearchCV,
                                     StratifiedKFold, cross_validate)
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score, f1_score, ConfusionMatrixDisplay)

from lib.praproses import praproses
from lib.labels import KELAS

SEED = 42


def _cm_png(yte, ypred, labels, judul) -> bytes:
    cm = confusion_matrix(yte, ypred, labels=labels)
    fig, ax = plt.subplots(figsize=(7, 6) if len(labels) > 2 else (4.5, 4))
    ConfusionMatrixDisplay(cm, display_labels=labels).plot(
        ax=ax, cmap="Blues", xticks_rotation=45, colorbar=False, values_format="d")
    ax.set_title(judul)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    return buf.getvalue()


def _evaluasi(nama, X_text, y, enam_kelas: bool):
    Xtr, Xte, ytr, yte = train_test_split(
        X_text, y, test_size=0.20, stratify=y, random_state=SEED)
    pipe = Pipeline_tfidf_nb()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    grid = GridSearchCV(pipe, param_grid={"nb__alpha": [0.01, 0.05, 0.1, 0.5, 1.0]},
                        scoring="f1_macro", cv=cv, n_jobs=-1)
    grid.fit(Xtr, ytr)
    model = grid.best_estimator_
    ypred = model.predict(Xte)
    if enam_kelas:
        labels = [k for k in KELAS if k in set(yte)]
    else:
        labels = ["cyberbullying", "non_cyberbullying"]
    rangkum = {
        "alpha": grid.best_params_["nb__alpha"],
        "f1_macro_cv": float(grid.best_score_),
        "akurasi": float(accuracy_score(yte, ypred)),
        "macro_f1": float(f1_score(yte, ypred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(yte, ypred, average="weighted", zero_division=0)),
        "laporan": classification_report(yte, ypred, labels=labels,
                                         output_dict=True, zero_division=0),
    }
    return rangkum, yte, ypred, labels


def Pipeline_tfidf_nb():
    from sklearn.pipeline import Pipeline
    return Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2)),
                     ("nb", MultinomialNB())])


def _validasi_silang(X_text, y, alpha):
    from sklearn.pipeline import Pipeline
    pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2)),
                     ("nb", MultinomialNB(alpha=alpha))])
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    r = cross_validate(pipe, X_text, y, cv=cv, scoring=["accuracy", "f1_macro"])
    a, f = r["test_accuracy"], r["test_f1_macro"]
    return {"akurasi_mean": float(a.mean()), "akurasi_std": float(a.std()),
            "macro_f1_mean": float(f.mean()), "macro_f1_std": float(f.std())}


def latih(df_berlabel, lapor=None):
    """Latih & evaluasi dua skema. df_berlabel: kolom 'teks' & 'label' (Indonesia).
    'lapor' opsional: fungsi(pesan) untuk progress di UI. Kembalikan dict."""
    def _log(msg):
        if lapor:
            lapor(msg)

    df = df_berlabel[df_berlabel["label"].isin(KELAS)].dropna(subset=["teks"]).copy()
    df = df.reset_index(drop=True)
    _log(f"Data berlabel valid: {len(df)}")

    _log("Praproses teks (7 tahap)...")
    df["clean"] = df["teks"].apply(praproses)
    df = df[df["clean"].str.strip() != ""].reset_index(drop=True)
    X_text = df["clean"]

    # A. enam kelas
    _log("Melatih & menguji skema ENAM KELAS...")
    m6, yte6, yp6, lab6 = _evaluasi("Enam kelas", X_text, df["label"], True)
    cm6_png = _cm_png(yte6, yp6, lab6, "Confusion Matrix - Naive Bayes (6 Kelas)")

    # B. biner
    _log("Melatih & menguji skema BINER...")
    y_biner = df["label"].map(lambda k: "non_cyberbullying" if k == "non_cyberbullying"
                              else "cyberbullying")
    m2, yte2, yp2, lab2 = _evaluasi("Biner", X_text, y_biner, False)
    baseline = float((yte2 == "non_cyberbullying").mean())
    m2["baseline"] = baseline
    cm2_png = _cm_png(yte2, yp2, ["cyberbullying", "non_cyberbullying"],
                      "Confusion Matrix - Naive Bayes (Biner)")

    # C. validasi silang 5-lipat (alpha 0.01)
    _log("Validasi silang 5-lipat...")
    cv6 = _validasi_silang(X_text, df["label"], 0.01)
    cv2 = _validasi_silang(X_text, y_biner, 0.01)

    # D. latih ulang di SELURUH data -> model final
    _log("Melatih model final di seluruh data...")
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
    Xall = tfidf.fit_transform(X_text)
    model_6 = MultinomialNB(alpha=0.01).fit(Xall, df["label"])
    y_biner_all = df["label"].map(lambda k: "non_cyberbullying" if k == "non_cyberbullying"
                                  else "cyberbullying")
    model_biner = MultinomialNB(alpha=0.01).fit(Xall, y_biner_all)

    metrik = {
        "n_data": int(len(df)),
        "distribusi": df["label"].value_counts().to_dict(),
        "enam_kelas": m6,
        "biner": m2,
        "cv_enam_kelas": cv6,
        "cv_biner": cv2,
    }
    _log("Selesai.")
    return {
        "metrik": metrik,
        "model_6": model_6,
        "model_biner": model_biner,
        "tfidf": tfidf,
        "cm6_png": cm6_png,
        "cm2_png": cm2_png,
    }
