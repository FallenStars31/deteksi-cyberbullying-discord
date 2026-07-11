# LAPORAN PERBAIKAN DAN PEMUTAKHIRAN SISTEM

**Deteksi Cyberbullying pada Platform Discord Menggunakan Natural Language Processing dan Naïve Bayes**
Naufal Ikhsan Erman — Teknik Informatika, UPI YPTK Padang · 11 Juli 2026

---

## Ringkasan

Pada tahap finalisasi kode, ditemukan dan diperbaiki sejumlah *bug* pada tahap **pembersihan data** dan **penyaringan kandidat pelabelan**; pelabelan juga diverifikasi ulang. Perbaikan ini mengubah komposisi data sehingga sebagian angka pada naskah perlu dimutakhirkan. Seluruh perubahan dilaporkan apa adanya, **tanpa data sintetis**. Seluruh angka "Sebelum" pada laporan ini telah **dicocokkan dan sesuai** dengan naskah skripsi (lihat Bagian 8).

---

## A. Kerangka / Urutan Kerja Sistem

Sistem berjalan sebagai *pipeline* enam tahap berurutan; keluaran satu tahap menjadi masukan tahap berikutnya.

```
[1] Pengumpulan Data                8 berkas CSV DiscordChatExporter (Server A/B/C/D)
          │
          ▼
[2] Pembersihan Data                01_pembersihan_data.py
     buang bot/emoji/kosong/tautan/duplikat, anonimisasi   →  hasil/data_bersih.csv  (49.584)
          │
          ▼
[3] Penyaringan Kandidat            02_penyaringan_pelabelan.py  (lexicon kata kasar)
     memunculkan pesan berindikasi   02b_penyaringan_minoritas.py (pola frasa minoritas)
          │
          ▼
[4] Pelabelan Manual                verifikasi manusia, 6 kelas, acuan pedoman_anotasi_v2.md
          │                          →  hasil/dataset_berlabel.csv  (1.940)
          ▼
[5] Praproses NLP + Naïve Bayes     03_nlp_naive_bayes.py
     7 tahap praproses → TF-IDF →     →  metrik + confusion matrix + model_nb*.joblib
     MultinomialNB (6 kelas & biner)
          │
          ▼
[6] Antarmuka Web                    04_antarmuka_streamlit.py  (2 tab: Deteksi & Evaluasi Model)
```

**Rincian tiap tahap:**

1. **Pengumpulan Data** — 8 kanal obrolan dari 4 server Discord diekspor dengan DiscordChatExporter (kolom: `AuthorID, Author, Date, Content, Attachments, Reactions`).
2. **Pembersihan Data** (`01`) — gabung 8 CSV → buang pesan bot/aplikasi → newline→spasi → hapus tautan → hapus emoji → anonimisasi mention & AuthorID → buang pesan kosong / hanya tautan / hanya emoji → buang duplikat.
3. **Penyaringan Kandidat** (`02`, `02b`) — `02` menormalkan slang lalu mencocokkan lexicon kata kasar + kata kunci ancaman; `02b` menyisir pola frasa kelas minoritas (exclusion/threat/hate_speech) yang sering tak memuat kata kasar. Keluaran = daftar kandidat untuk ditinjau.
4. **Pelabelan Manual** — peneliti melabeli kandidat ke 6 kelas mengikuti aturan prioritas `threat > hate_speech > harassment > exclusion > insult`; kehadiran kata kasar tidak otomatis dianggap cyberbullying.
5. **Praproses NLP + Naïve Bayes** (`03`) — tujuh tahap praproses (*cleaning → case folding → tokenisasi (regex) → normalisasi slang → stopword removal (Sastrawi) → stemming (Sastrawi) → TF-IDF*), lalu Multinomial Naïve Bayes. Oversampling & TF-IDF berada **di dalam** `imblearn.Pipeline` agar tidak bocor saat *cross-validation*. Dua skema dievaluasi: enam kelas dan biner.
6. **Antarmuka Web** (`04`) — tab *Deteksi* memprediksi satu pesan (dua skema) sesuai rancangan Gambar 4.10; tab *Evaluasi Model* menampilkan confusion matrix dan tabel metrik tiap kelas.

---

## 1. Latar Belakang Perbaikan

Peninjauan menyeluruh atas kode menemukan kekeliruan pada tahap 2 dan 3 yang menurunkan kualitas data. Perbaikan bersifat memperbaiki ketepatan metodologi, bukan mempercantik angka.

## 2. Perbaikan pada Tahap Pembersihan Data (`01`)

1. **Penyaringan bot/aplikasi.** Versi awal gagal membuang pesan bot karena pola nama terhalang *discriminator* `#dddd`. Perbaikan mendeteksi bot melalui `#dddd` (sejak 2023 hanya dimiliki bot) + daftar nama bot populer → **351 pesan bot** dibuang (sebelumnya 0).
2. **Penghapusan emoji.** Versi awal tidak menangani emoji. Perbaikan menghapus emoji Unicode & emoji khusus Discord (`:nama:`) dari teks, dan membuang pesan yang hanya berisi emoji (**4.011 pesan**).
3. **Pemetaan server.** Kunci `"ALTER_LIFE"` (garis bawah) tidak cocok dengan nama berkas `"ALTER LIFE"` (spasi) sehingga Server A tercatat `"Server ?"`. Perbaikan membuat pemetaan tahan beda spasi/garis bawah.

## 3. Perbaikan pada Tahap Penyaringan Kandidat (`02`, `02b`)

1. **Frasa ancaman tak terdeteksi.** Kata kunci multi-kata (`"gua cari"`, `"awas kamu"`) tak pernah cocok karena pencocokan hanya per kata tunggal; kini frasa dicocokkan benar.
2. **Urutan prioritas keliru.** Diselaraskan dengan pedoman: `threat > hate_speech > harassment > exclusion > insult` (sebelumnya menaruh insult di atas exclusion).
3. **Kebocoran normalisasi.** Kata kasar tertentu hilang saat normalisasi (mis. `tai`→`tahi`) dan pemanjangan huruf (`anjingg`) tak dikenali; kini keduanya ditangani.
4. **Sampel tidak acak.** Kandidat minoritas diambil dari urutan awal (bias); kini sampel acak dengan seed tetap.

---

## 4. Pemutakhiran Hasil Pembersihan Data

> Memutakhirkan **Tabel 3.1** dan **Tabel 4.1** naskah ("Hasil Pembersihan Data").

**Tabel 1. Perbandingan hasil pembersihan data**

| Tahap | Sebelum | Sesudah |
|---|--:|--:|
| Pesan mentah (gabungan 8 kanal) | 71.445 | 71.445 |
| Dibuang: pesan bot/aplikasi | 0 | **351** |
| Dibuang: pesan kosong | 2.194 | 2.087 |
| Dibuang: hanya tautan/lampiran | 714 | 714 |
| Dibuang: hanya emoji | – | **4.011** |
| Dibuang: duplikat | 17.898 | 14.698 |
| **Pesan bersih (siap diproses)** | **50.639** | **49.584** |

*Duplikat menurun karena pesan emoji-only yang dahulu terhitung sebagai duplikat kini menjadi kategori tersendiri.*

**Tabel 2. Sebaran pesan bersih per server**

| Server | Sebelum | Sesudah |
|---|--:|--:|
| Server A | 47.117 | 46.224 |
| Server B | 411 | 393 |
| Server C | 2.085 | 1.991 |
| Server D | 1.026 | 976 |

## 5. Pemutakhiran Dataset Berlabel

> Memutakhirkan **Tabel 4.2** naskah ("Distribusi Jumlah Data per Kelas").

Perbaikan penyaringan memunculkan kandidat minoritas yang sebelumnya terlewat, dan seluruh label diverifikasi ulang secara manual. Dataset bertambah dari **1.868** menjadi **1.940** pesan.

**Tabel 3. Distribusi kelas dataset berlabel**

| Kelas | Sebelum | Sesudah |
|---|--:|--:|
| non_cyberbullying | 1.609 | 1.604 |
| insult | 168 | 223 |
| harassment | 40 | 52 |
| threat | 23 | 24 |
| exclusion | 21 | 28 |
| hate_speech | 7 | 9 |
| **Total** | **1.868** | **1.940** |

## 6. Hasil Pengujian Terbaru

Pengujian ulang: *split* 80:20 *stratified*, seed 42. Hasil **enam kelas membaik** (macro-F1 0,254 → **0,338**) berkat pelabelan yang lebih cermat, sedangkan **biner sedikit menurun** (akurasi 0,890 → **0,850**) karena data kini lebih bersih dan memuat lebih banyak kasus perbatasan. **Skema biner tetap hasil utama** (di atas baseline 0,823 & target 75%).

**Tabel 4. Ringkasan perbandingan (akurasi & macro-F1)**

| Skema | Metrik | Sebelum | Sesudah |
|---|---|--:|--:|
| Enam kelas | Akurasi | 0,609 | 0,557 |
| Enam kelas | macro-F1 | 0,254 | **0,338** |
| Biner | Akurasi | 0,890 | 0,850 |
| Biner | macro-F1 | 0,703 | 0,663 |
| Baseline | "selalu normal" | 0,860 | 0,823 |

> Memutakhirkan **Tabel 5.1** naskah ("Hasil Pengujian Klasifikasi Enam Kelas").

**Tabel 5. Hasil pengujian klasifikasi enam kelas (baru)**

| Kelas | Precision | Recall | F1-score | Data uji |
|---|--:|--:|--:|--:|
| insult | 0,431 | 0,622 | 0,509 | 45 |
| threat | 0,250 | 0,800 | 0,381 | 5 |
| hate_speech | 0,000 | 0,000 | 0,000 | 2 |
| harassment | 0,316 | 0,600 | 0,414 | 10 |
| exclusion | 0,024 | 0,400 | 0,045 | 5 |
| non_cyberbullying | 0,895 | 0,548 | 0,680 | 312 |
| **Akurasi** | | | **0,557** | 379 |
| Rata-rata macro | 0,319 | 0,495 | 0,338 | |
| Rata-rata weighted | 0,800 | 0,557 | 0,637 | |

> Memutakhirkan **Tabel 5.2** naskah ("Hasil Pengujian Klasifikasi Biner").

**Tabel 6. Hasil pengujian klasifikasi biner (baru)**

| Kelas | Precision | Recall | F1-score | Data uji |
|---|--:|--:|--:|--:|
| cyberbullying | 0,667 | 0,299 | 0,412 | 67 |
| non_cyberbullying | 0,865 | 0,968 | 0,914 | 312 |
| **Akurasi** | | | **0,850** | 379 |
| Rata-rata macro | 0,766 | 0,633 | 0,663 | |
| Rata-rata weighted | 0,830 | 0,850 | 0,825 | |

Kelas langka (`hate_speech`, `exclusion`) tetap berkinerja rendah/nol karena datanya sangat sedikit (9 & 28 contoh); dilaporkan apa adanya. **Gambar 5.1 & 5.2** (confusion matrix) di naskah perlu diganti dengan berkas baru di `hasil/`.

## 7. Implementasi Antarmuka

Antarmuka web (Streamlit) memiliki dua tab. Tab **Deteksi** dibuat **persis Gambar 4.10** (header, kolom teks, tombol "Deteksi", kotak hasil + diagram batang probabilitas) dan menyediakan **dua skema** (enam kelas & biner). Tab **Evaluasi Model** menampilkan **langsung** kedua confusion matrix (Gambar 5.1 & 5.2) beserta tabel metrik tiap kelas, dibaca dari `hasil/metrik.json`.

---

## 8. Verifikasi Konsistensi dengan Naskah

Angka "Sebelum" pada laporan ini diverifikasi langsung terhadap isi naskah `Skripsi_...LENGKAP.docx`:

| Elemen naskah | Nilai di naskah | Cocok? |
|---|---|:--:|
| Tabel 3.1 / 4.1 (pembersihan) | 71.445 → 50.639; bot 0; kosong 2.194; tautan 714; duplikat 17.898 | ✔ |
| Tabel 4.2 (distribusi) | 1.868 (1.609/168/40/23/21/7) | ✔ |
| Tabel 5.1 (enam kelas) | akurasi 0,609; macro-F1 0,254; weighted 0,687 | ✔ |
| Tabel 5.2 (biner) | akurasi 0,890; macro-F1 0,703; precision 0,720; recall 0,346 | ✔ |

**Daftar yang perlu dimutakhirkan di naskah Word:**

- [ ] **Tabel 3.1** dan **Tabel 4.1** → ganti dengan Tabel 1 (tambah baris bot 351 & emoji 4.011; bersih 49.584).
- [ ] Teks sebaran per server → Tabel 2 (A 46.224 / B 393 / C 1.991 / D 976).
- [ ] **Tabel 4.2** → ganti dengan Tabel 3 (total 1.940).
- [ ] **Tabel 5.1** → ganti dengan Tabel 5 (akurasi 0,557; macro-F1 0,338).
- [ ] **Tabel 5.2** → ganti dengan Tabel 6 (akurasi 0,850; macro-F1 0,663).
- [ ] **Gambar 5.1 & 5.2** → ganti dengan `hasil/confusion_matrix_6kelas.png` & `hasil/confusion_matrix_biner.png` yang baru.
- [ ] Kalimat naratif yang menyebut `1.868`, `50.639`, `60,9%`, `0,890`, `bot 0` → sesuaikan.
- [ ] Kalimat "Pipeline NLP … menggunakan library **NLTK** dan PySastrawi" → ganti: tokenisasi berbasis **regex**, stopword & stemming dengan **Sastrawi** (kode tidak memakai NLTK).

## 9. Penutup

Seluruh perbaikan telah diselaraskan antara program, dokumentasi (README & konteks), dan angka hasil sehingga konsisten dan dapat direproduksi (jalankan `03` untuk mereproduksi metrik BAB V). Perubahan dilakukan demi ketepatan metodologi dan kejujuran pelaporan.
