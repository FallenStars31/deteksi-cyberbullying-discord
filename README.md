# Kode Skripsi — Deteksi Cyberbullying Discord (Naïve Bayes)

Kode ini mengikuti metodologi **BAB III–V** skripsi (Naufal Ikhsan Erman,
Teknik Informatika, UPI YPTK Padang). Semua angka di kode, README, dan naskah
sudah diselaraskan agar konsisten dan dapat direproduksi (seed = 42).

## Struktur folder
```
proyek/
├─ 01_pembersihan_data.py         # Pengumpulan & Pembersihan Data (Tabel 4.1)
├─ 02_penyaringan_pelabelan.py    # Penyaringan kandidat kata kasar (tahap 1)
├─ 02b_penyaringan_minoritas.py   # Penyaringan pola frasa kelas minoritas (tahap 2)
├─ 03_nlp_naive_bayes.py          # Praproses NLP + Multinomial NB + evaluasi (BAB V)
├─ 04_antarmuka_streamlit.py      # Antarmuka web 2 skema (6 kelas & biner), persis Gambar 4.10
├─ requirements.txt
├─ pedoman_anotasi_v2.md          # Pedoman pelabelan 6 kelas (acuan anotasi)
├─ datachatdiscord/               # 8 berkas CSV hasil DiscordChatExporter
├─ kamus/                         # kamus normalisasi & lexicon (lihat di bawah)
└─ hasil/                         # output otomatis + dataset_berlabel.csv
```

## Instalasi (Python 3.9+)
```bat
python -m venv .venv
.venv\Scripts\activate           # Windows;  di Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Kamus di folder `kamus/`
- `colloquial-indonesian-lexicon.csv` — Salsabila dkk. (2018), repo `nasalsabila/kamus-alay`
- `abusive.csv` — Ibrohim & Budi (2019); ditambah daftar *elang* (Chan dkk., 2020)

## Urutan menjalankan
```bat
python 01_pembersihan_data.py        # -> hasil/data_bersih.csv + cetak Tabel 4.1
python 02_penyaringan_pelabelan.py   # -> hasil/dataset_untuk_dilabeli.csv (kandidat tahap 1)
python 02b_penyaringan_minoritas.py  # -> hasil/kandidat_minoritas.csv    (kandidat tahap 2)
# >> Labeli MANUAL sesuai pedoman_anotasi_v2.md, gabung, simpan sebagai
#    hasil/dataset_berlabel.csv  (kolom: msg_id, server, author_anon, teks, label)
python 03_nlp_naive_bayes.py         # -> metrik 6 kelas & biner + 2 confusion matrix + model
streamlit run 04_antarmuka_streamlit.py  # -> antarmuka web (pilih skema: Enam Kelas / Biner)
```
> Dataset final yang dipakai di skripsi sudah disertakan sebagai
> `hasil/dataset_berlabel.csv` (1.940 pesan). Menjalankan `03` langsung akan
> mereproduksi angka BAB V.

## Ringkasan data (konsisten dengan naskah)
- Pesan mentah (8 kanal): **71.445** → bersih: **49.584**
  (dibuang: bot/aplikasi 351, kosong 2.087, tautan/lampiran 714, emoji 4.011, duplikat 14.698)
- Sebaran server bersih: A 46.224, B 393, C 1.991, D 976
- Dataset berlabel final: **1.940** pesan
  - non_cyberbullying 1.604, insult 223, harassment 52, threat 24, exclusion 28, hate_speech 9

## Pelabelan (6 kelas)
- Kelas: `insult, threat, hate_speech, harassment, exclusion, non_cyberbullying`
- **Aturan prioritas (bila 1 pesan kena >1 kategori):**
  `threat > hate_speech > harassment > exclusion > insult`
- **Identitas (SARA/gender/disabilitas) selalu → hate_speech.**
- Adanya kata kasar TIDAK otomatis cyberbullying; label final ditentukan verifikasi manusia.
- Detail lengkap ada di `pedoman_anotasi_v2.md`.

## Praproses (7 tahap, sesuai BAB III–IV)
Cleaning → Case Folding → Tokenisasi → Normalisasi slang → Stopword Removal →
Stemming (Sastrawi) → TF-IDF (n-gram 1–2, min_df=2).

## Hasil pengujian (split 80:20 stratified, seed 42) — apa adanya
| Skenario | Akurasi | macro-F1 | weighted-F1 |
|---|---|---|---|
| **Enam kelas** (oversampling di data latih) | 0,557 | 0,338 | 0,637 |
| **Biner** (cyberbullying vs non, tanpa resampling) | 0,850 | 0,663 | 0,825 |
| *baseline "selalu normal"* | *0,823* | — | — |

- **Hasil utama = skema BINER** (melampaui target 75% & baseline 0,823;
  precision cyberbullying 0,667, recall 0,299).
- Pada enam kelas, kelas langka (hate_speech, exclusion) berkinerja rendah/0
  karena data sangat sedikit — dilaporkan **jujur apa adanya, tanpa data sintetis**.

## Catatan penting (perbaikan yang sudah diterapkan)
1. **Kebocoran data (data leakage) diperbaiki:** oversampling & TF-IDF kini
   dijalankan DI DALAM `imblearn.Pipeline` sehingga hanya pada lipatan latih saat
   cross-validation. (Versi lama meng-oversample sebelum CV → skor CV palsu ~0,92.)
2. **Skema biner tidak memakai oversampling** karena rasio lebih ringan dan
   oversampling justru menurunkan presisi.
3. Angka di **naskah, README, dan output kode sudah sama**. Jika data diubah,
   jalankan ulang `03` lalu samakan kembali angka di naskah.

## Keterbatasan (jujur)
Ketidakseimbangan data ekstrem; deteksi berbasis teks tidak menangkap perundungan
di voice chat; automod Discord telah menyapu sebagian kata kunci eksplisit; dan
penyaringan berbasis lexicon dapat melewatkan sindiran/sarkasme.

## Hosting (Streamlit Community Cloud)
Aplikasi web di-hosting gratis lewat **Streamlit Community Cloud**, yang deploy
langsung dari repo GitHub ini.

Berkas yang dipakai saat runtime: `04_antarmuka_streamlit.py` (main),
`03_nlp_naive_bayes.py` (fungsi praproses), `requirements.txt`, `kamus/`,
`.streamlit/config.toml`, dan model di `hasil/` (`*.joblib`, `metrik.json`,
`confusion_matrix_*.png`). Data pesan mentah TIDAK diunggah (lihat `.gitignore`).

Langkah deploy:
1. Buat repo GitHub (disarankan **private** — melindungi data & naskah).
2. Push proyek ini ke repo tersebut.
3. Buka https://share.streamlit.io → **New app** → pilih repo & branch.
4. **Main file path:** `04_antarmuka_streamlit.py`
5. **Deploy.** Streamlit Cloud memasang `requirements.txt` lalu menjalankan app.
