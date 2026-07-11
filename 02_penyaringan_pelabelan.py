# -*- coding: utf-8 -*-
"""
02_penyaringan_pelabelan.py
Tahap Pelabelan Data semi-otomatis (sesuai BAB III - Pelabelan Data, Gambar 3.2).

Alur:
  data_bersih.csv
   -> normalisasi slang (Colloquial Indonesian Lexicon, Salsabila dkk. 2018)
   -> pencocokan lexicon (kata kasar: Ibrohim & Budi 2019 + elang Chan dkk. 2020,
      disesuaikan domain Discord) + kata kunci ancaman
   -> tandai KANDIDAT vs NORMAL
   -> ambil SEMUA kandidat + 1.000 normal acak (seed tetap) = dataset utk dilabeli
   -> simpan berkas pelabelan (kolom 'label' dikosongkan utk diisi manual)

Kelas (multi-kelas, 1 label per pesan). Aturan prioritas bila >1 indikasi:
  threat > hate_speech > harassment > exclusion > insult
Kelas: insult, threat, hate_speech, harassment, exclusion, non_cyberbullying

Catatan: kehadiran kata kasar TIDAK otomatis = cyberbullying. Penandaan kamus
hanya penyaring prioritas; LABEL FINAL ditentukan verifikasi manusia.
"""

import os
import re
import pandas as pd

FOLDER_OUT   = "hasil"
FOLDER_KAMUS = "kamus"
SEED         = 42          # seed tetap agar dapat direproduksi
JUMLAH_NORMAL = 1000       # jumlah pesan normal acak yang ditambahkan

# ---------------------------------------------------------------------------
# Pemuatan kamus. Unduh berkas asli lalu letakkan di folder 'kamus/':
#   - colloquial-indonesian-lexicon.csv  (github.com/nasalsabila/kamus-alay)
#   - abusive.csv                        (github.com/okkyibrohim/...abusive...)
#   - (elang) daftar kata kasar tambahan
# Jika berkas tidak ada, dipakai contoh kecil bawaan agar skrip tetap jalan.
# ---------------------------------------------------------------------------
def muat_kamus_normalisasi() -> dict:
    path = os.path.join(FOLDER_KAMUS, "colloquial-indonesian-lexicon.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        # berkas asli punya kolom 'slang' dan 'formal'
        kol = {c.lower(): c for c in df.columns}
        s, f = kol.get("slang"), kol.get("formal")
        if s and f:
            # BUG: 10.675 slang ganda -> dict(zip) hanya simpan mapping terakhir.
            # Ambil kemunculan pertama agar deterministik.
            df = df.drop_duplicates(subset=s, keep="first")
            return dict(zip(df[s].astype(str), df[f].astype(str)))
    # fallback contoh
    return {"gw": "saya", "gue": "saya", "lo": "kamu", "lu": "kamu",
            "bgt": "banget", "gk": "tidak", "ga": "tidak", "yg": "yang",
            "udh": "sudah", "dgn": "dengan", "aja": "saja", "knp": "kenapa"}


def muat_lexicon_kasar() -> set:
    kata = set()
    path = os.path.join(FOLDER_KAMUS, "abusive.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        kol = df.columns[0]
        kata |= set(df[kol].astype(str).str.lower())
    if not kata:
        # fallback contoh (disesuaikan domain Discord; "anjir" dsb DIBUANG karena seruan)
        kata = {"anjing", "babi", "bangsat", "kontol", "memek", "goblok",
                "tolol", "idiot", "bego", "sampah", "yatim", "miskin"}
    # buang kata seru/politik yang tidak relevan
    for buang in {"anjir", "anjay", "wkwk"}:
        kata.discard(buang)
    return kata


# kata kunci ANCAMAN (ancaman sering tidak memuat kata kasar)
KATA_ANCAMAN = {"bunuh", "hajar", "datengin", "datangin", "gebuk", "tikam",
                "tusuk", "habisi", "cari kamu", "awas kamu", "gua cari"}

TOKEN_RE = re.compile(r"[a-z]+")
ELONG_RE = re.compile(r"(.)\1+")        # ciutkan huruf berulang: "kontoool" -> "kontol"


def normalisasi(teks: str, kamus: dict) -> str:
    tok = TOKEN_RE.findall(str(teks).lower())
    return " ".join(kamus.get(t, t) for t in tok)


def main():
    df = pd.read_csv(os.path.join(FOLDER_OUT, "data_bersih.csv"), keep_default_na=False)
    kamus  = muat_kamus_normalisasi()
    kasar  = muat_lexicon_kasar()

    # Pisahkan target 1-kata (dicek via himpunan token) dan frasa multi-kata
    # (dicek via regex batas-kata). BUG lama: frasa spt "gua cari" TAK pernah
    # cocok karena deteksi hanya irisan token unigram.
    target_uni = {w for w in (kasar | KATA_ANCAMAN) if " " not in w}
    frasa = sorted((w for w in KATA_ANCAMAN if " " in w), key=len, reverse=True)
    FRASA_RE = (re.compile("|".join(r"\b" + re.escape(p) + r"\b" for p in frasa))
                if frasa else None)

    teks_norm = df["teks"].apply(lambda s: normalisasi(s, kamus))

    def kata_terdeteksi(t_norm: str, t_asli: str):
        # token ternormalisasi + token ASLI (lindungi kata spt "tai" yang
        # dinormalisasi jadi "tahi") + varian elongasi diciutkan ("anjingg"->"anjing").
        low = str(t_asli).lower()
        tok = set(t_norm.split()) | set(TOKEN_RE.findall(low))
        tok |= {ELONG_RE.sub(r"\1", w) for w in tok}
        hit = set(tok & target_uni)
        if FRASA_RE:
            hit |= set(FRASA_RE.findall(low))     # frasa dicek pd teks ASLI (slang belum diubah)
        return ";".join(sorted(hit))

    df["kata_terdeteksi"] = [kata_terdeteksi(n, a) for n, a in zip(teks_norm, df["teks"])]
    df["hasil_screening"] = df["kata_terdeteksi"].apply(
        lambda s: "kandidat" if s else "normal")

    kandidat = df[df["hasil_screening"] == "kandidat"].copy()
    normal   = df[df["hasil_screening"] == "normal"].copy()

    print("=" * 50)
    print("HASIL PENYARINGAN (Gambar 3.2)")
    print("=" * 50)
    print(f"Total pesan bersih      : {len(df):>8,}")
    print(f"Pesan KANDIDAT          : {len(kandidat):>8,}")
    print(f"Pesan NORMAL            : {len(normal):>8,}")

    # ambil 1.000 normal acak (seed tetap) -> reproducible
    n_amb = min(JUMLAH_NORMAL, len(normal))
    normal_sampel = normal.sample(n=n_amb, random_state=SEED)

    dataset = pd.concat([kandidat, normal_sampel], ignore_index=True)
    dataset["label"] = ""          # diisi manual: 6 kelas
    dataset = dataset.sample(frac=1, random_state=SEED).reset_index(drop=True)

    out = os.path.join(FOLDER_OUT, "dataset_untuk_dilabeli.csv")
    dataset.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nDataset untuk dilabeli   : {len(dataset):>8,} "
          f"({len(kandidat)} kandidat + {n_amb} normal)")
    print(f"Disimpan -> {out}")
    print("\nIsi kolom 'label' secara manual dengan salah satu dari:")
    print("  insult | threat | hate_speech | harassment | exclusion | non_cyberbullying")
    print("Aturan prioritas: threat > hate_speech > harassment > exclusion > insult")


if __name__ == "__main__":
    main()
