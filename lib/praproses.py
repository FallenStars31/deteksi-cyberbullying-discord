# -*- coding: utf-8 -*-
"""
lib/praproses.py
Tujuh tahap praproses NLP (dipisah dari 03_nlp_naive_bayes.py agar dipakai ulang
oleh halaman pelatihan & prediksi). Urutan PERSIS naskah BAB III:

  1. Cleaning     : buang mention, tautan, emoji, angka, tanda baca
  2. Case Folding : huruf kecil
  3. Tokenisasi   : pecah jadi token
  4. Normalisasi  : slang -> baku (Colloquial Indonesian Lexicon)
  5. Stopword Removal (stopword Bahasa Indonesia)
  6. Stemming     : Sastrawi
  (7. TF-IDF dilakukan di tahap pemodelan, bukan di sini.)

Menyediakan:
  - praproses(teks) -> str                (dipakai pelatihan & prediksi)
  - praproses_bertahap(teks) -> list      (hasil tiap tahap, utk contoh BAB IV/UI)
"""

import os
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import pandas as pd

FOLDER_KAMUS = "kamus"

_stemmer = StemmerFactory().create_stemmer()
_stopword = set(StopWordRemoverFactory().get_stop_words())
_stem_cache = {}  # cache agar cepat saat memproses ribuan pesan

URL_RE     = re.compile(r"https?://\S+|www\.\S+")
NONALFA_RE = re.compile(r"[^a-z\s]")     # sisakan huruf saja
TOKEN_RE   = re.compile(r"[a-z]+")


def _muat_kamus_normalisasi() -> dict:
    path = os.path.join(FOLDER_KAMUS, "colloquial-indonesian-lexicon.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        kol = {c.lower(): c for c in df.columns}
        s = kol.get("slang")
        f = kol.get("formal") or kol.get("baku")
        if s and f:
            # IDENTIK dgn 03_nlp_naive_bayes.py (tanpa dedup: mapping terakhir
            # menang) agar hasil praproses & metrik SAMA PERSIS dengan naskah.
            return dict(zip(df[s].astype(str), df[f].astype(str)))
    return {"gw": "saya", "gue": "saya", "lo": "kamu", "lu": "kamu", "bgt": "banget",
            "gk": "tidak", "ga": "tidak", "yg": "yang", "udh": "sudah", "aja": "saja"}


KAMUS_NORM = _muat_kamus_normalisasi()


def _stem(w: str) -> str:
    if w not in _stem_cache:
        _stem_cache[w] = _stemmer.stem(w)
    return _stem_cache[w]


def praproses(teks: str) -> str:
    """Tujuh tahap praproses -> string bersih siap TF-IDF."""
    t = str(teks)
    t = URL_RE.sub(" ", t)                        # (1) cleaning: tautan
    t = re.sub(r"@\w+", " ", t)                   # (1) cleaning: mention
    t = t.lower()                                 # (2) case folding
    t = NONALFA_RE.sub(" ", t)                    # (1) cleaning: emoji/tanda baca/angka
    tok = TOKEN_RE.findall(t)                     # (3) tokenisasi
    tok = [KAMUS_NORM.get(w, w) for w in tok]     # (4) normalisasi slang -> baku
    tok = [w for w in tok if w not in _stopword]  # (5) stopword removal
    tok = [_stem(w) for w in tok]                 # (6) stemming (Sastrawi)
    return " ".join(tok)


def praproses_bertahap(teks: str) -> list:
    """Kembalikan hasil TIAP tahap sebagai list of (nama_tahap, hasil).
    Dipakai untuk contoh 'sebelum/sesudah' di BAB IV dan tampilan edukasi di UI."""
    langkah = []
    asli = str(teks)
    langkah.append(("Pesan mentah", asli))

    t = URL_RE.sub(" ", asli)
    t = re.sub(r"@\w+", " ", t)
    langkah.append(("1. Cleaning — buang tautan & mention", re.sub(r"\s+", " ", t).strip()))

    t = t.lower()
    langkah.append(("2. Case Folding — huruf kecil", re.sub(r"\s+", " ", t).strip()))

    t = re.sub(r"\s+", " ", NONALFA_RE.sub(" ", t)).strip()
    langkah.append(("1. Cleaning — buang emoji/angka/tanda baca", t))

    tok = TOKEN_RE.findall(t)
    langkah.append(("3. Tokenisasi", tok))

    tok_norm = [KAMUS_NORM.get(w, w) for w in tok]
    ubah = [f"{a}→{b}" for a, b in zip(tok, tok_norm) if a != b]
    langkah.append(("4. Normalisasi (slang→baku)", tok_norm))
    langkah.append(("   · kata dinormalisasi", ubah or ["(tidak ada)"]))

    tok_stop = [w for w in tok_norm if w not in _stopword]
    dibuang = [w for w in tok_norm if w in _stopword]
    langkah.append(("5. Stopword Removal", tok_stop))
    langkah.append(("   · stopword dibuang", dibuang or ["(tidak ada)"]))

    tok_stem = [_stem(w) for w in tok_stop]
    ubah_s = [f"{a}→{b}" for a, b in zip(tok_stop, tok_stem) if a != b]
    langkah.append(("6. Stemming (Sastrawi)", tok_stem))
    langkah.append(("   · kata di-stem", ubah_s or ["(tidak ada)"]))

    langkah.append(("Hasil akhir (masuk TF-IDF)", " ".join(tok_stem)))
    return langkah
