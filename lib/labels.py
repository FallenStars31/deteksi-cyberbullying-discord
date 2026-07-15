# -*- coding: utf-8 -*-
"""
lib/labels.py
Konstanta kelas & pemetaan label. Kelas memakai Bahasa Indonesia (kecuali
`non_cyberbullying` yang sudah jadi istilah umum). Dipakai seragam oleh semua
halaman web, penyaringan, pelatihan, dan prediksi.
"""

# 6 kelas resmi (5 jenis cyberbullying + 1 normal).
KELAS = [
    "penghinaan",
    "ancaman",
    "ujaran_kebencian",
    "pelecehan",
    "pengucilan",
    "non_cyberbullying",
]

# Urutan prioritas bila 1 pesan kena >1 kategori (tinggi -> rendah).
# ancaman > ujaran_kebencian > pelecehan > pengucilan > penghinaan
PRIORITAS = ["ancaman", "ujaran_kebencian", "pelecehan", "pengucilan", "penghinaan"]

# Peta label LAMA (Inggris) & typo -> label BARU (Indonesia).
# Dipakai saat migrasi dataset_berlabel.csv lama ke database.
PETA_LABEL = {
    # Inggris -> Indonesia
    "insult": "penghinaan",
    "threat": "ancaman",
    "hate_speech": "ujaran_kebencian",
    "harassment": "pelecehan",
    "exclusion": "pengucilan",
    "non_cyberbullying": "non_cyberbullying",
    # typo lama yang pernah ditemukan
    "harasment": "pelecehan",
    "insuly": "penghinaan",
    "exclusiom": "pengucilan",
    "exlucion": "pengucilan",
    "exlusion": "pengucilan",
    "non_cyberbuulying": "non_cyberbullying",
}

# Nama tampil (judul) untuk UI.
NAMA_TAMPIL = {
    "penghinaan": "Penghinaan",
    "ancaman": "Ancaman",
    "ujaran_kebencian": "Ujaran Kebencian",
    "pelecehan": "Pelecehan",
    "pengucilan": "Pengucilan",
    "non_cyberbullying": "Non-Cyberbullying",
    "cyberbullying": "Cyberbullying",
}

# Label ringkas untuk bar chart probabilitas.
RINGKAS = {
    "penghinaan": "hina",
    "ancaman": "ancam",
    "ujaran_kebencian": "kebencian",
    "pelecehan": "leceh",
    "pengucilan": "kucil",
    "non_cyberbullying": "non_cb",
    "cyberbullying": "bully",
}


def ke_indonesia(label: str) -> str:
    """Ubah label lama/typo -> label Indonesia baku. Yang sudah baku dibiarkan."""
    s = str(label).strip()
    return PETA_LABEL.get(s, s)


def valid(label: str) -> bool:
    return ke_indonesia(label) in KELAS
