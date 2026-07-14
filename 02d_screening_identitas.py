# -*- coding: utf-8 -*-
"""
02d_screening_identitas.py
Penyaringan TERARAH untuk kelas HATE_SPEECH (ujaran kebencian).

Kelas hate_speech paling langka (cold-start): model & keyword screening umum
melewatkannya. Karena aturan "identitas selalu -> hate_speech", cara paling
tepat adalah MEMINDAI penanda identitas (suku/agama/ras/gender/orientasi/politik)
langsung pada kolam pesan belum-berlabel, lalu meninjau manual mana yang
benar-benar menyerang (hate_speech) vs sekadar menyebut identitas (non_cb).

Output: hasil/kandidat_identitas.csv  (kolom 'label' dikosongkan utk diisi manual)
"""

import os
import re
import pandas as pd

FOLDER_OUT = "hasil"

# Penanda identitas (grup non-capturing, batas kata). Bukan daftar lengkap;
# fokus istilah yang paling sering dipakai menyerang di data.
KATEGORI = {
    "suku": r"\b(?:jawa|sunda|batak|madura|padang|minang|bugis|aceh|ambon|papua|"
            r"dayak|betawi|banjar|manado|nias|flores|melayu)\b",
    "ras": r"\b(?:cina|china|tionghoa|aseng|arab|india|keling|negro|bule)\b",
    "agama": r"\b(?:kafir|murtad|sesat|nasrani|yahudi|syiah|kristen|hindu|budha)\b",
    "gender": r"\b(?:banci|bencong|bences|homo|lesbi|lesbian|gay|waria|ladyboy|tomboy)\b",
    "politik": r"\b(?:kadrun|cebong|kampret|buzzer)\b",
}
RX = {k: re.compile(v) for k, v in KATEGORI.items()}


def main():
    df = pd.read_csv(os.path.join(FOLDER_OUT, "data_bersih.csv"), keep_default_na=False)

    # kecualikan yang sudah dilabeli + yang sudah muncul di kandidat lain
    exclude = set()
    for f in ("dataset_berlabel.csv", "kandidat_model.csv"):
        p = os.path.join(FOLDER_OUT, f)
        if os.path.exists(p):
            exclude |= set(pd.read_csv(p, keep_default_na=False)["teks"].astype(str))
    df = df[~df["teks"].astype(str).isin(exclude)].reset_index(drop=True)

    low = df["teks"].astype(str).str.lower()

    def tandai(t):
        return ";".join(k for k, rx in RX.items() if rx.search(t))

    df["kategori_identitas"] = low.apply(tandai)
    cand = df[df["kategori_identitas"] != ""].copy()
    cand["label"] = ""

    cols = [c for c in ["msg_id", "server", "teks", "kategori_identitas", "label"]
            if c in cand.columns]
    out = os.path.join(FOLDER_OUT, "kandidat_identitas.csv")
    cand[cols].to_csv(out, index=False, encoding="utf-8-sig")

    print(f"Kandidat ber-penanda identitas: {len(cand)} -> {out}")
    print("Per kategori:", dict(cand["kategori_identitas"].value_counts()))
    print("Tinjau manual: yang MENYERANG identitas -> hate_speech; "
          "sebutan netral (mis. 'aku orang jawa') -> non_cyberbullying.")


if __name__ == "__main__":
    main()
