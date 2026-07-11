# -*- coding: utf-8 -*-
"""
02b_penyaringan_minoritas.py
Penyaringan TAMBAHAN untuk kelas minoritas yang sering TIDAK memuat kata kasar:
exclusion (pengucilan), threat (ancaman), hate_speech (ujaran kebencian).

Penyaringan kata kasar (skrip 02) melewatkan pesan seperti
"kamu ngapain disini gausah ikut sini" (exclusion tanpa kata kasar).
Skrip ini menyisir data bersih memakai POLA FRASA untuk memunculkan kandidat,
lalu kamu labeli manual ('saran_kelas' hanya petunjuk; bisa jadi non_cyberbullying).

Output: hasil/kandidat_minoritas.csv
"""

import os, re
import pandas as pd

FOLDER_OUT = "hasil"
MAKS_PER_KELAS = 300
SEED = 42                  # seed tetap agar pengambilan sampel dapat direproduksi

# Pola memakai grup non-capturing (?:...) agar tidak memicu warning pandas.
POLA = {
 "exclusion": [
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
 "threat": [
   r"\bawas\s+(?:lu|lo|kamu|ya|aja|nanti)",
   r"\b(?:gua|gw|gue|aku|ku)\s+(?:datengin|datangin|samperin|hajar|gebuk|pukul|bunuh|habisin|tikam|tusuk|sumpahin|laporin|sebar)",
   r"\b(?:gua|gw|gue|aku|ku)\s+cari\s+(?:lu|lo|kamu|kau)",
   r"\b(?:mati|matek)\s+(?:lu|lo|kau|kamu)\b",
   r"\brasain\s+(?:aja|nanti|akibat)",
   r"\bjangan\s+harap\s+(?:selamat|aman|hidup)\b",
   r"\bgua\s+(?:gak|ga)\s+segan\b",
 ],
 # hate_speech: pemicu identitas (SARA) untuk DITINJAU MANUAL.
 # Lengkapi dengan lexicon hate speech (Ibrohim & Budi, 2019, label HS).
 "hate_speech": [
   r"\b(?:kafir|murtad|ajaran sesat|sesat lu)\b",
   r"\b(?:aseng|cina lu|dasar cina)\b",
   r"\b(?:kadrun|cebong)\b",
   r"\b(?:banci lu|bencong|homo lu)\b",
   r"\bdasar\s+(?:jawa|batak|padang|ambon|papua|madura|cina|arab)\b",
 ],
}

def main():
    df = pd.read_csv(os.path.join(FOLDER_OUT, "data_bersih.csv"), keep_default_na=False)
    teks_low = df["teks"].astype(str).str.lower()
    labeled = os.path.join(FOLDER_OUT, "dataset_berlabel.csv")
    sudah = (set(pd.read_csv(labeled, keep_default_na=False)["teks"].astype(str))
             if os.path.exists(labeled) else set())

    # Urutan prioritas utk dedup lintas-kelas: threat > hate_speech > exclusion.
    # (Pesan yg kena >1 pola disarankan ke kelas prioritas tertinggi; identitas
    # SARA selalu menang atas exclusion.)
    prioritas = ["threat", "hate_speech", "exclusion"]

    rows = []
    for kelas in prioritas:
        rx = re.compile("|".join(POLA[kelas]))
        hit = df[teks_low.str.contains(rx, na=False, regex=True)]
        hit = hit[~hit["teks"].astype(str).isin(sudah)]
        # BUG lama: .head() ambil 300 pertama (bias urutan). Kini sampel acak.
        n_amb = min(MAKS_PER_KELAS, len(hit))
        ambil = hit.sample(n=n_amb, random_state=SEED).copy() if n_amb else hit.copy()
        ambil["saran_kelas"] = kelas
        rows.append(ambil)
        print(f"{kelas:12s}: {len(hit):>5} kandidat (diambil {len(ambil)})")

    out = pd.concat(rows, ignore_index=True).drop_duplicates(subset="teks")
    out["label"] = ""
    cols = [c for c in ["msg_id","server","teks","saran_kelas","label"] if c in out.columns]
    out = out[cols]
    path = os.path.join(FOLDER_OUT, "kandidat_minoritas.csv")
    out.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"\nTotal kandidat unik: {len(out)} -> {path}")
    print("Labeli kolom 'label' manual (boleh non_cyberbullying bila ternyata bukan).")

if __name__ == "__main__":
    main()
