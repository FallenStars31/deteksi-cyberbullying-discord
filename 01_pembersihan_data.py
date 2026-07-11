# -*- coding: utf-8 -*-
"""
01_pembersihan_data.py
Tahap Pengumpulan & Pembersihan Data (sesuai BAB III, Tabel 3.1).

Alur (sesuai skripsi):
  Gabungkan 8 berkas CSV  ->  buang pesan bot/aplikasi (discriminator #dddd + nama bot)
  ->  newline jadi spasi  ->  hapus tautan  ->  hapus emoji (unicode & custom :nama:)
  ->  anonimisasi mention (@nama -> @user) & AuthorID (-> U0001, ...)
  ->  buang pesan kosong  ->  buang pesan hanya tautan/lampiran
  ->  buang pesan hanya emoji  ->  buang duplikat  ->  data bersih (siap diproses)

Output:
  - hasil/data_bersih.csv      (kolom: msg_id, server, author_anon, teks)
  - mencetak Tabel 3.1 (jumlah pesan tiap tahap) + sebaran per server
"""

import os
import re
import glob
import pandas as pd

# ---------------------------------------------------------------------------
# KONFIGURASI  (sesuaikan dengan folder di komputermu, mis. D:\skripsi\...)
# ---------------------------------------------------------------------------
FOLDER_CSV = "datachatdiscord"     # folder berisi 8 berkas CSV hasil DiscordChatExporter
FOLDER_OUT = "hasil"
os.makedirs(FOLDER_OUT, exist_ok=True)

# Pemetaan nama berkas -> Server A/B/C/D (untuk menjaga anonimitas komunitas).
# Sesuaikan kata kunci di kiri dengan nama berkas CSV-mu.
PETA_SERVER = {
    "ALTER_LIFE": "Server A",
    "AWEKENING":  "Server B",
    "Affection":  "Server C",
    "hikari":     "Server D",
}

URL_RE     = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"@[\w.]+")          # @nama -> @user
NEWLINE_RE = re.compile(r"[\r\n]+")

# Custom emoji Discord: <:nama:id>, <a:nama:id>, dan bentuk :nama: (wajib ada
# huruf, supaya jam seperti "10:30:00" tidak ikut terhapus).
CUSTOM_EMOJI_RE = re.compile(
    r"<a?:[A-Za-z0-9_]+:\d+>|:(?=[A-Za-z0-9_]*[A-Za-z])[A-Za-z0-9_]{2,}:"
)

# Emoji unicode (blok-blok utama: emoticon, pictograph, simbol, bendera, dsb).
EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"   # bendera (regional indicator)
    "\U0001F300-\U0001FAFF"   # emoticon, pictograph, transport, simbol tambahan
    "\U00002600-\U000026FF"   # misc symbols  (matahari, petir, dll)
    "\U00002700-\U000027BF"   # dingbats      (centang, hati, bintang, dll)
    "\U00002B00-\U00002BFF"   # bintang/panah tebal
    "\U00002300-\U000023FF"   # jam, gembok, kontrol media
    "\U00002190-\U000021FF"   # panah
    "\U0000FE00-\U0000FE0F"   # variation selector
    "\U00002122\U00002139"    # (TM), (info)
    "\U0000200D"              # zero-width joiner (perekat emoji majemuk)
    "]+"
)

# Nama bot populer (pengaman tambahan, selain deteksi discriminator #dddd).
NAMA_BOT_RE = re.compile(
    r"\b(mee6|carl[- ]?bot|dyno|probot|rythm|jockie|groovy|arcane|mudae|"
    r"unbelievaboat|dank\s?memer|pok.?two|nqn|epic\s?rpg|reaction\s?bot)\b",
    re.IGNORECASE,
)
# Ciri akun bot/aplikasi: masih memakai discriminator "#dddd". Akun manusia sudah
# tidak memilikinya sejak Discord menghapus discriminator pada 2023.
DISCRIMINATOR_RE = re.compile(r"#\d{3,4}$")


def tentukan_server(nama_file: str) -> str:
    # Normalisasi beda spasi/garis-bawah agar kunci "ALTER_LIFE" cocok dengan
    # nama berkas "ALTER LIFE - ..." (dan sebaliknya).
    nf = nama_file.lower().replace("_", " ")
    for kunci, server in PETA_SERVER.items():
        if kunci.lower().replace("_", " ") in nf:
            return server
    return "Server ?"


def main():
    berkas = sorted(glob.glob(os.path.join(FOLDER_CSV, "*.csv")))
    if not berkas:
        raise SystemExit(f"Tidak ada CSV di folder '{FOLDER_CSV}'.")

    # 1) Gabungkan 8 berkas CSV --------------------------------------------
    frames = []
    for f in berkas:
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
        df["server"] = tentukan_server(os.path.basename(f))
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)
    n_mentah = len(data)

    # 2) Buang pesan dari akun bot / aplikasi ------------------------------
    #    DiscordChatExporter tidak punya kolom penanda bot, tetapi akun
    #    bot/aplikasi MASIH memakai discriminator "#dddd" (akun manusia sudah
    #    tidak lagi sejak 2023). Deteksi utama lewat discriminator, ditambah
    #    pencocokan nama bot populer sebagai pengaman.
    author = data["Author"].fillna("").str.strip()
    is_bot = author.apply(
        lambda a: bool(DISCRIMINATOR_RE.search(a) or NAMA_BOT_RE.search(a))
    )
    n_bot = int(is_bot.sum())
    data = data[~is_bot].copy()

    # 3) Praproses teks berlapis -------------------------------------------
    #    Dibuat bertahap agar tiap tahap pembersihan bisa dihitung terpisah.
    #    Emoji diganti spasi (bukan dihapus) supaya kata tidak menyatu, mis.
    #    "keren<emoji>banget" -> "keren banget".
    raw         = data["Content"].fillna("").apply(lambda s: NEWLINE_RE.sub(" ", s).strip())
    tanpa_link  = raw.apply(lambda s: URL_RE.sub("", s).strip())            # buang tautan
    tanpa_emoji = tanpa_link.apply(                                          # buang emoji
        lambda s: EMOJI_RE.sub(" ", CUSTOM_EMOJI_RE.sub(" ", s)).strip())
    teks_final  = tanpa_emoji.apply(lambda s: MENTION_RE.sub("@user", s))    # @nama -> @user
    teks_final  = teks_final.apply(lambda s: re.sub(r"\s+", " ", s).strip())
    data["teks"] = teks_final

    #    Anonimisasi AuthorID -> kode anonim U0001, U0002, ...
    id_unik = {aid: f"U{idx:04d}" for idx, aid in enumerate(data["AuthorID"].unique(), start=1)}
    data["author_anon"] = data["AuthorID"].map(id_unik)

    # 4) Tandai pesan yang dibuang (tiap pesan masuk TEPAT satu kategori) ---
    is_kosong     = raw.eq("")                                            # Content asli kosong
    is_link_only  = (~is_kosong) & tanpa_link.eq("")                      # hanya tautan/lampiran
    is_emoji_only = (~is_kosong) & (~is_link_only) & tanpa_emoji.eq("")   # hanya emoji
    n_kosong = int(is_kosong.sum())
    n_link   = int(is_link_only.sum())
    n_emoji  = int(is_emoji_only.sum())
    data = data[~(is_kosong | is_link_only | is_emoji_only)].copy()

    # 5) Buang duplikat (mencegah data leakage) ----------------------------
    sebelum = len(data)
    data = data.drop_duplicates(subset="teks", keep="first").copy()
    n_dup = sebelum - len(data)

    n_bersih = len(data)

    # ---- Susun output final ----------------------------------------------
    data = data.reset_index(drop=True)
    data.insert(0, "msg_id", [f"M{idx:05d}" for idx in range(1, len(data) + 1)])
    out = data[["msg_id", "server", "author_anon", "teks"]]
    out.to_csv(os.path.join(FOLDER_OUT, "data_bersih.csv"), index=False, encoding="utf-8-sig")

    # ---- Cetak Tabel 3.1 --------------------------------------------------
    print("=" * 56)
    print("TABEL 3.1  HASIL PEMBERSIHAN DATA")
    print("=" * 56)
    print(f"{'Pesan mentah (gabungan 8 kanal)':40s}{n_mentah:>10,}")
    print(f"{'Dibuang: pesan bot/aplikasi':40s}{n_bot:>10,}")
    print(f"{'Dibuang: pesan kosong':40s}{n_kosong:>10,}")
    print(f"{'Dibuang: hanya tautan/lampiran':40s}{n_link:>10,}")
    print(f"{'Dibuang: hanya emoji':40s}{n_emoji:>10,}")
    print(f"{'Dibuang: duplikat':40s}{n_dup:>10,}")
    print("-" * 56)
    print(f"{'Pesan bersih (siap diproses)':40s}{n_bersih:>10,}")
    print("=" * 56)
    print("\nSebaran per server:")
    for srv, jml in out["server"].value_counts().sort_index().items():
        print(f"  {srv:12s}: {jml:>8,}")
    print(f"\nDisimpan -> {os.path.join(FOLDER_OUT, 'data_bersih.csv')}")


if __name__ == "__main__":
    main()
