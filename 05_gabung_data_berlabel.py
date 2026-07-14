# -*- coding: utf-8 -*-
"""
05_gabung_data_berlabel.py
Menggabungkan SEMUA data berlabel dari berbagai tahap penyaringan menjadi
SATU berkas: hasil/dataset_berlabel.csv.

LATAR: pelabelan dilakukan berlapis dari empat tahap penyaringan yang berbeda
(`02` kata kasar, `02b` pola minoritas, `02c` dibantu model, `02d` penanda
identitas), masing-masing menghasilkan berkas kandidat yang dilabeli manual.
Skrip ini menyatukannya secara konsisten & dapat direproduksi.

ATURAN PENGGABUNGAN (berlaku utk SEMUA sumber):
  1. Baca setiap berkas berlabel.
  2. Bakukan kolom 'label' -> perbaiki typo, buang yang kosong/tidak valid
     (hanya 6 kelas resmi yang diterima).
  3. Bersihkan emoji pada 'teks' (samakan dgn data_bersih; pesan yg jadi kosong dibuang).
  4. Isi 'author_anon' dari data_bersih berdasarkan 'teks'.
  5. Gabung semua -> BUANG DUPLIKAT teks (satu teks = satu baris; sumber lebih awal menang).
  6. Beri 'msg_id' ulang secara urut, simpan sebagai satu CSV.

Sifat: IDEMPOTEN — menjalankan ulang dgn sumber yang sama menghasilkan berkas
yang sama (dedup menjaga tak ada penggandaan). Aman dijalankan tiap ronde baru.
"""

import os
import re
import pandas as pd

FOLDER_OUT = "hasil"

# Urutan sumber = urutan prioritas saat dedup (yang lebih awal dipertahankan).
# Setiap entri = (keterangan tahap, path berkas berlabel).
SUMBER = [
    ("akumulasi ronde sebelumnya (02/02b + augmentasi)", "hasil/dataset_berlabel.csv"),
    ("tahap 02c — dibantu model (active learning)",       "hasil/kandidat_model.csv"),
    ("tahap 02d — pindai penanda identitas (hate_speech)", "hasil/kandidat_identitas.csv"),
]

KELAS = {"insult", "threat", "hate_speech", "harassment", "exclusion", "non_cyberbullying"}

# Peta typo pelabelan -> label baku (ditemukan saat verifikasi).
TYPO = {
    "harasment": "harassment", "exclusiom": "exclusion", "exlucion": "exclusion",
    "exlusion": "exclusion", "insuly": "insult", "non_cyberbuulying": "non_cyberbullying",
}

# --- regex emoji IDENTIK dgn 01_pembersihan_data.py (agar teks konsisten) ---
CUSTOM_EMOJI_RE = re.compile(
    r"<a?:[A-Za-z0-9_]+:\d+>|:(?=[A-Za-z0-9_]*[A-Za-z])[A-Za-z0-9_]{2,}:")
EMOJI_RE = re.compile(
    "[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF\U00002600-\U000026FF"
    "\U00002700-\U000027BF\U00002B00-\U00002BFF\U00002300-\U000023FF"
    "\U00002190-\U000021FF\U0000FE00-\U0000FE0F\U00002122\U00002139\U0000200D]+")


def bersih_emoji(s: str) -> str:
    s = EMOJI_RE.sub(" ", CUSTOM_EMOJI_RE.sub(" ", str(s)))
    return re.sub(r"\s+", " ", s).strip()


def main():
    bersih = pd.read_csv(os.path.join(FOLDER_OUT, "data_bersih.csv"), keep_default_na=False)
    anon = dict(zip(bersih["teks"].astype(str), bersih["author_anon"].astype(str)))

    frames = []
    print("Sumber berlabel yang digabung:")
    for ket, path in SUMBER:
        if not os.path.exists(path):
            print(f"  - {ket}: (dilewati, tak ada) {path}")
            continue
        d = pd.read_csv(path, keep_default_na=False)
        # (2) bakukan label
        d["label"] = d["label"].astype(str).str.strip().replace(TYPO)
        d = d[d["label"].isin(KELAS)].copy()
        # (3) bersihkan emoji, buang yang jadi kosong
        d["teks"] = d["teks"].astype(str).apply(bersih_emoji)
        d = d[d["teks"] != ""]
        # (4) isi author_anon dari data_bersih
        if "author_anon" not in d.columns:
            d["author_anon"] = ""
        d["author_anon"] = d.apply(
            lambda r: r["author_anon"] if r["author_anon"] else anon.get(r["teks"], ""),
            axis=1)
        srv = d["server"] if "server" in d.columns else ""
        frames.append(pd.DataFrame({"server": srv, "author_anon": d["author_anon"],
                                    "teks": d["teks"], "label": d["label"]}))
        print(f"  - {ket}: {len(d)} baris berlabel valid")

    gab = pd.concat(frames, ignore_index=True)
    sebelum = len(gab)
    # (5) buang duplikat teks (sumber lebih awal dipertahankan)
    gab = gab.drop_duplicates(subset="teks", keep="first").reset_index(drop=True)
    # (6) beri msg_id ulang
    gab.insert(0, "msg_id", [f"M{i:05d}" for i in range(1, len(gab) + 1)])
    gab = gab[["msg_id", "server", "author_anon", "teks", "label"]]

    out = os.path.join(FOLDER_OUT, "dataset_berlabel.csv")
    gab.to_csv(out, index=False, encoding="utf-8-sig")

    print(f"\nDuplikat teks dibuang saat gabung: {sebelum - len(gab)}")
    print(f"Total data berlabel gabungan     : {len(gab)}  -> {out}")
    print("Distribusi kelas:")
    for k, n in gab["label"].value_counts().items():
        print(f"  {k:18s}: {n}")


if __name__ == "__main__":
    main()
