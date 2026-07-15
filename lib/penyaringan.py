# -*- coding: utf-8 -*-
"""
lib/penyaringan.py
Penyaringan kandidat untuk pelabelan (gabungan strategi 02, 02b, 02c, 02d),
label memakai Bahasa Indonesia.

Strategi (urut sesuai kesepakatan — yang ada lexicon dulu):
  TAHAP A (berbasis daftar kata / lexicon):
    - penghinaan       : lexicon kata kasar (abusive.csv)
    - ujaran_kebencian : penanda identitas (SARA/gender/politik)  [aturan: identitas -> hate]
  TAHAP B (metode sendiri, tak ada lexicon):
    - ancaman   : kata + pola frasa ancaman
    - pengucilan: pola frasa pengucilan
  TAHAP C (dibantu model / active learning): saring_model()

Fungsi:
  saring(df_bersih, sudah=set()) -> DataFrame kandidat
  saring_model(df_bersih, tfidf, model_biner, model_6, sudah, ...) -> DataFrame
Catatan: 'saran_kelas' hanya PETUNJUK; label final ditentukan verifikasi manusia.
"""

import os
import re
import pandas as pd

from lib.praproses import KAMUS_NORM
from lib.labels import PRIORITAS

FOLDER_KAMUS = "kamus"
TOKEN_RE = re.compile(r"[a-z]+")
ELONG_RE = re.compile(r"(.)\1+")

# ---- lexicon kata kasar (-> penghinaan) ----
def muat_lexicon_kasar() -> set:
    kata = set()
    path = os.path.join(FOLDER_KAMUS, "abusive.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        kata |= set(df.iloc[:, 0].astype(str).str.lower())
    if not kata:
        kata = {"anjing", "babi", "bangsat", "kontol", "memek", "goblok",
                "tolol", "idiot", "bego", "sampah"}
    for buang in {"anjir", "anjay", "wkwk"}:
        kata.discard(buang)
    return kata

# ---- kata + pola ANCAMAN ----
KATA_ANCAMAN = {"bunuh", "hajar", "datengin", "datangin", "gebuk", "tikam",
                "tusuk", "habisi", "gua cari", "cari kamu", "awas kamu"}

POLA = {
    "ancaman": [
        r"\bawas\s+(?:lu|lo|kamu|ya|aja|nanti)",
        r"\b(?:gua|gw|gue|aku|ku)\s+(?:datengin|datangin|samperin|hajar|gebuk|pukul|bunuh|habisin|tikam|tusuk|sumpahin|laporin|sebar)",
        r"\b(?:gua|gw|gue|aku|ku)\s+cari\s+(?:lu|lo|kamu|kau)",
        r"\b(?:mati|matek)\s+(?:lu|lo|kau|kamu)\b",
        r"\brasain\s+(?:aja|nanti|akibat)",
        r"\bjangan\s+harap\s+(?:selamat|aman|hidup)\b",
        r"\bgua\s+(?:gak|ga)\s+segan\b",
    ],
    "pengucilan": [
        r"\b(?:ga|gak|nggak|ngga|kaga|kagak)\s*usah\s+(?:ikut|gabung|kesini|ke sini|disini|di sini|masuk|nimbrung|join)",
        r"ngapain\s+(?:lu|lo|kamu|kau|disini|di sini|kesini|ke sini|ikut|join|masuk)",
        r"\bjangan\s+(?:ajak|ikut|masuk|invite|masukin|ngajak|gabung)",
        r"\b(?:keluar|pergi|minggir|cabut)\s+(?:aja|sana|lu|lo|dari sini)",
        r"\b(?:usir|keluarin|tendang)\b",
        r"\b(?:tinggalin|cuekin|abaikan|kacangin)\s+aja",
        r"\b(?:bukan|ga|gak|kaga)\s+urusan\s+(?:lu|lo|kamu)",
        r"\bsok\s+(?:ikut|asik|kenal|akrab)\b",
        r"\b(?:ga|gak)\s+ada\s+yang\s+(?:ngajak|manggil|nanya)\b",
        r"\bsiapa\s+yang\s+(?:ngajak|manggil|nanya)\s+(?:lu|lo|kamu)\b",
    ],
}
RX_POLA = {k: re.compile("|".join(v)) for k, v in POLA.items()}

# ---- penanda IDENTITAS (-> ujaran_kebencian) ----
KATEGORI_IDENTITAS = {
    "suku": r"\b(?:jawa|sunda|batak|madura|padang|minang|bugis|aceh|ambon|papua|"
            r"dayak|betawi|banjar|manado|nias|flores|melayu)\b",
    "ras": r"\b(?:cina|china|tionghoa|aseng|arab|india|keling|negro|bule)\b",
    "agama": r"\b(?:kafir|murtad|sesat|nasrani|yahudi|syiah|kristen|hindu|budha)\b",
    "gender": r"\b(?:banci|bencong|bences|homo|lesbi|lesbian|gay|waria|ladyboy|tomboy)\b",
    "politik": r"\b(?:kadrun|cebong|kampret|buzzer)\b",
}
RX_IDENTITAS = re.compile("|".join(KATEGORI_IDENTITAS.values()))


def _normalisasi(teks: str) -> str:
    tok = TOKEN_RE.findall(str(teks).lower())
    return " ".join(KAMUS_NORM.get(t, t) for t in tok)


def _pilih_prioritas(kelas_terdeteksi: set) -> str:
    """Ambil kelas prioritas tertinggi dari himpunan kelas yang terdeteksi."""
    for k in PRIORITAS:                       # ancaman > ujaran_kebencian > ... > penghinaan
        if k in kelas_terdeteksi:
            return k
    return "penghinaan"


def saring(df_bersih: pd.DataFrame, sudah=None) -> pd.DataFrame:
    """Saring kandidat memakai lexicon + pola + identitas.
    'sudah' = himpunan teks yang SUDAH dilabeli (dikecualikan)."""
    sudah = sudah or set()
    kasar = muat_lexicon_kasar()
    target_uni = {w for w in kasar if " " not in w}
    frasa_ancaman = [w for w in KATA_ANCAMAN if " " in w]
    FRASA_RE = re.compile("|".join(r"\b" + re.escape(p) + r"\b" for p in frasa_ancaman)) \
        if frasa_ancaman else None
    uni_ancaman = {w for w in KATA_ANCAMAN if " " not in w}

    rows = []
    msg_ids = df_bersih["msg_id"] if "msg_id" in df_bersih.columns else [""] * len(df_bersih)
    servers = df_bersih["server"] if "server" in df_bersih.columns else [""] * len(df_bersih)
    for mid, srv, teks in zip(msg_ids, servers, df_bersih["teks"].astype(str)):
        if teks in sudah:
            continue
        low = teks.lower()
        norm = _normalisasi(teks)
        tok = set(norm.split()) | set(TOKEN_RE.findall(low))
        tok |= {ELONG_RE.sub(r"\1", w) for w in tok}

        kelas_hit = set()
        strategi = []
        bukti = []

        # penghinaan (lexicon kasar)
        hit_kasar = tok & target_uni
        if hit_kasar:
            kelas_hit.add("penghinaan"); strategi.append("lexicon_kasar")
            bukti += sorted(hit_kasar)

        # ancaman (kata + pola)
        hit_ancam = tok & uni_ancaman
        if FRASA_RE:
            hit_ancam |= set(FRASA_RE.findall(low))
        if hit_ancam or RX_POLA["ancaman"].search(low):
            kelas_hit.add("ancaman"); strategi.append("pola_ancaman")
            bukti += sorted(hit_ancam)

        # ujaran_kebencian (identitas)
        if RX_IDENTITAS.search(low):
            kelas_hit.add("ujaran_kebencian"); strategi.append("identitas")

        # pengucilan (pola)
        if RX_POLA["pengucilan"].search(low):
            kelas_hit.add("pengucilan"); strategi.append("pola_pengucilan")

        if not kelas_hit:
            continue
        rows.append({
            "msg_id": mid,
            "server": srv,
            "teks": teks,
            "saran_kelas": _pilih_prioritas(kelas_hit),
            "strategi": ";".join(strategi),
            "kata_terdeteksi": ";".join(sorted(set(bukti))),
            "p_bully": None,
            "label": "",
        })
    return pd.DataFrame(rows)


def saring_model(df_bersih, tfidf, model_biner, model_6, sudah=None,
                 ambil_top=400, ambang=0.60):
    """Active learning: pakai model terlatih untuk memunculkan pesan ber-probabilitas
    cyberbullying tinggi yang LOLOS lexicon. Butuh model & tfidf yang sudah dilatih."""
    from lib.praproses import praproses
    sudah = sudah or set()
    df = df_bersih[~df_bersih["teks"].astype(str).isin(sudah)].copy().reset_index(drop=True)
    df["clean"] = df["teks"].apply(praproses)
    df = df[df["clean"].str.strip() != ""].reset_index(drop=True)
    if df.empty:
        return pd.DataFrame()

    X = tfidf.transform(df["clean"])
    kelas_biner = list(model_biner.classes_)
    i_bully = kelas_biner.index("cyberbullying") if "cyberbullying" in kelas_biner else 0
    df["p_bully"] = model_biner.predict_proba(X)[:, i_bully].round(3)
    df["saran_kelas"] = model_6.predict(X)

    df = df.sort_values("p_bully", ascending=False).reset_index(drop=True)
    kandidat = df[df["p_bully"] >= ambang]
    if len(kandidat) < ambil_top:
        kandidat = df.head(ambil_top)
    kandidat = kandidat.copy()
    kandidat["strategi"] = "model_active_learning"
    kandidat["kata_terdeteksi"] = ""
    kandidat["label"] = ""
    cols = ["msg_id", "server", "teks", "saran_kelas", "strategi",
            "kata_terdeteksi", "p_bully", "label"]
    return kandidat[[c for c in cols if c in kandidat.columns]]
