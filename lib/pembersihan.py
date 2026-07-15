# -*- coding: utf-8 -*-
"""
lib/pembersihan.py
Logika pembersihan data (dipisah dari 01_pembersihan_data.py) agar bisa dipanggil
dari halaman web. Alur & aturan IDENTIK dengan naskah (Tabel 3.1):

  gabung CSV -> buang bot (discriminator #dddd + nama bot) -> newline jadi spasi
  -> buang tautan -> buang emoji -> anonimisasi (@user, U0001) -> buang kosong
  -> buang hanya-tautan -> buang hanya-emoji -> buang duplikat.

Fungsi utama:
  bersihkan(frames) -> (df_bersih, statistik)
    frames : list of (nama_file, DataFrame mentah) — kolom DiscordChatExporter
             (AuthorID, Author, Date, Content, Attachments, Reactions)
"""

import re
import pandas as pd

PETA_SERVER = {
    "ALTER_LIFE": "Server A",
    "AWEKENING":  "Server B",
    "Affection":  "Server C",
    "hikari":     "Server D",
}

URL_RE     = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"@[\w.]+")
NEWLINE_RE = re.compile(r"[\r\n]+")
CUSTOM_EMOJI_RE = re.compile(
    r"<a?:[A-Za-z0-9_]+:\d+>|:(?=[A-Za-z0-9_]*[A-Za-z])[A-Za-z0-9_]{2,}:")
EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF\U00002600-\U000026FF"
    "\U00002700-\U000027BF\U00002B00-\U00002BFF\U00002300-\U000023FF"
    "\U00002190-\U000021FF\U0000FE00-\U0000FE0F\U00002122\U00002139\U0000200D"
    "]+")
NAMA_BOT_RE = re.compile(
    r"\b(mee6|carl[- ]?bot|dyno|probot|rythm|jockie|groovy|arcane|mudae|"
    r"unbelievaboat|dank\s?memer|pok.?two|nqn|epic\s?rpg|reaction\s?bot)\b",
    re.IGNORECASE)
DISCRIMINATOR_RE = re.compile(r"#\d{3,4}$")


def tentukan_server(nama_file: str) -> str:
    nf = nama_file.lower().replace("_", " ")
    for kunci, server in PETA_SERVER.items():
        if kunci.lower().replace("_", " ") in nf:
            return server
    return "Server ?"


def bersihkan(frames):
    """frames: list of (nama_file, df_mentah). Kembalikan (df_bersih, statistik)."""
    berkas = []
    for nama_file, df in frames:
        df = df.copy()
        df["server"] = tentukan_server(nama_file)
        berkas.append(df)
    data = pd.concat(berkas, ignore_index=True)
    n_mentah = len(data)

    # 2) buang bot/aplikasi (discriminator #dddd + nama bot)
    author = data.get("Author", pd.Series([""] * len(data))).fillna("").astype(str).str.strip()
    is_bot = author.apply(lambda a: bool(DISCRIMINATOR_RE.search(a) or NAMA_BOT_RE.search(a)))
    n_bot = int(is_bot.sum())
    data = data[~is_bot].copy()

    # 3) praproses teks berlapis
    raw = data.get("Content", pd.Series([""] * len(data))).fillna("").apply(
        lambda s: NEWLINE_RE.sub(" ", str(s)).strip())
    tanpa_link = raw.apply(lambda s: URL_RE.sub("", s).strip())
    tanpa_emoji = tanpa_link.apply(
        lambda s: EMOJI_RE.sub(" ", CUSTOM_EMOJI_RE.sub(" ", s)).strip())
    teks_final = tanpa_emoji.apply(lambda s: MENTION_RE.sub("@user", s))
    teks_final = teks_final.apply(lambda s: re.sub(r"\s+", " ", s).strip())
    data["teks"] = teks_final

    # anonimisasi AuthorID -> U0001, ...
    if "AuthorID" in data.columns:
        id_unik = {aid: f"U{idx:04d}" for idx, aid in enumerate(data["AuthorID"].unique(), start=1)}
        data["author_anon"] = data["AuthorID"].map(id_unik)
    else:
        data["author_anon"] = ""

    # 4) tandai pesan yang dibuang (tiap pesan tepat satu kategori)
    is_kosong = raw.eq("")
    is_link_only = (~is_kosong) & tanpa_link.eq("")
    is_emoji_only = (~is_kosong) & (~is_link_only) & tanpa_emoji.eq("")
    n_kosong = int(is_kosong.sum())
    n_link = int(is_link_only.sum())
    n_emoji = int(is_emoji_only.sum())
    data = data[~(is_kosong | is_link_only | is_emoji_only)].copy()

    # 5) buang duplikat (cegah data leakage)
    sebelum = len(data)
    data = data.drop_duplicates(subset="teks", keep="first").copy()
    n_dup = sebelum - len(data)
    n_bersih = len(data)

    data = data.reset_index(drop=True)
    data.insert(0, "msg_id", [f"M{idx:05d}" for idx in range(1, len(data) + 1)])
    df_bersih = data[["msg_id", "server", "author_anon", "teks"]]

    statistik = {
        "mentah": n_mentah,
        "bot": n_bot,
        "kosong": n_kosong,
        "tautan": n_link,
        "emoji": n_emoji,
        "duplikat": n_dup,
        "bersih": n_bersih,
        "sebaran_server": df_bersih["server"].value_counts().sort_index().to_dict(),
    }
    return df_bersih, statistik
