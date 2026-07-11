# PEDOMAN ANOTASI (PELABELAN DATA) — v2
### Deteksi Cyberbullying pada Platform Discord menggunakan Naïve Bayes

Dokumen ini menjadi acuan agar pelabelan konsisten, objektif, dan dapat
dipertanggungjawabkan. Versi 2 memperjelas **prosedur keputusan** dan
memperbaiki **aturan prioritas** agar kasus multi-sinyal (mis. hinaan + pengucilan,
atau pengucilan berbasis suku) tidak lagi ambigu.

---

## 1. Aturan Umum

- **Multi-kelas, satu label per pesan.** Terdapat 6 label: 5 kategori cyberbullying + 1 normal.
- Pelabelan berdasarkan **isi teks**. Konteks percakapan sekitar (penulis & waktu sama) boleh jadi pertimbangan.
- **Prinsip kunci:** *adanya kata kasar TIDAK otomatis cyberbullying.* Sebuah pesan
  cyberbullying bila serangan/kata kasar **diterapkan pada sasaran manusia**.
- **Sasaran harus MANUSIA** (individu atau kelompok identitas). Serangan ke
  **benda, game, server, brand/perusahaan, produk, tokoh publik, atau diri sendiri → `non_cyberbullying`.**
  - Contoh non_cb: "game ini sampah", "server tolol lag mulu", "tsel goblok sinyal jelek", "tolol ni keyboard".
- **Kode label ditulis persis:** `insult`, `threat`, `hate_speech`, `harassment`,
  `exclusion`, `non_cyberbullying`. (Gunakan `non_cyberbullying`, **bukan** `non_cb`, agar konsisten dengan pipeline.)

---

## 2. Prosedur Keputusan (POHON KEPUTUSAN)

Periksa **berurutan dari atas**. Berhenti pada langkah pertama yang cocok.

**Langkah 0 — Sasarannya siapa?**
Benda / game / server / brand / institusi / tokoh publik / diri sendiri / tanpa sasaran
→ **`non_cyberbullying`**.

**Langkah 1 — Ada ancaman menyakiti (fisik/psikis)?**
"mati lu", "gua samperin ke rumah", "berantem kita", "awas lu nanti"
→ **`threat`**

**Langkah 2 — Serangan / pengucilan berbasis IDENTITAS (SARA, gender, disabilitas)?**
Menyebut suku/agama/ras/gender/orientasi/disabilitas sebagai dasar serangan atau penolakan
→ **`hate_speech`** *(identitas selalu menang atas insult/exclusion)*

**Langkah 3 — Inti pesan mengeluarkan/menolak seseorang dari kelompok?**
"gausah ikut", "ngapain lu disini", "keluar sana", "jangan diajak dia"
→ **`exclusion`**

**Langkah 4 — Menyerang/mengganggu seseorang secara BERULANG / terus-menerus?**
→ **`harassment`**

**Langkah 5 — Hinaan/celaan langsung ke seseorang?**
"bacot [nama]", "tolol lu", "goblok kau", "dasar bego"
→ **`insult`**

**Langkah 6 — Selain semua di atas** → **`non_cyberbullying`**

---

## 3. Aturan Prioritas (bila 1 pesan kena >1 kategori)

> **threat > hate_speech > harassment > exclusion > insult**

**Perubahan dari v1:** posisi **exclusion dinaikkan di atas insult**. Alasannya,
pesan yang **intinya mengucilkan** tetapi memakai makian (mis. "bacot lu gausah ikut")
lebih tepat dinilai sebagai `exclusion` (tindakan utamanya), bukan `insult`.

---

## 4. Definisi & Contoh Tiap Kategori

**a. `insult` (Penghinaan).** Merendahkan/mencela seseorang secara langsung.
Contoh: "dasar bodoh, gak ada gunanya lo di sini".

**b. `threat` (Ancaman).** Mengancam menyakiti, eksplisit/implisit.
Contoh: "awas ya, nanti gua samperin ke rumah lo".

**c. `hate_speech` (Ujaran Kebencian).** Menyerang/mendiskriminasi berdasarkan
identitas: suku, agama, ras, golongan, gender, orientasi seksual, disabilitas.
Contoh: "orang [suku X] emang gak pantes di sini".

**d. `harassment` (Pelecehan).** Mengganggu/mempermalukan/menyerang seseorang
secara **terus-menerus** hingga menimbulkan rasa tidak nyaman/terancam.
Contoh: "dari tadi gua bilang diem, muka lo emang minta digangguin terus".

**e. `exclusion` (Pengucilan).** Sengaja mengucilkan/mengeluarkan seseorang dari kelompok.
Contoh: "udah jangan diajak dia, ga usah dianggep".

**f. `non_cyberbullying` (Normal).** Obrolan biasa, candaan akrab tak menyerang,
pertanyaan, umpatan tanpa sasaran manusia, serangan ke benda/game/diri sendiri.
Contoh: "anjir capek banget hari ini wkwk", "gg gais mantap mainnya".

---

## 5. Aturan Khusus Kata Umpatan (bacot / goblok / tolol / anjing / kontol)

Kata-kata ini paling sering bikin label tidak konsisten. Pakai aturan berikut:

- **Diarahkan ke orang** → minimal `insult` (naik ke kategori lebih tinggi bila ada
  identitas/ancaman/pengucilan).
  - "bacot [nama]" / "goblok lu" / "tolol kau" → `insult`.
- **Adu bacot / bercanda timbal-balik / ada penanda tawa (wkwk, 🤣, :v) tanpa korban jelas**
  → `non_cyberbullying`.
  - "yuk adu bacot", "klean adu bacot sambil divideoin" → `non_cyberbullying`.
- **Untuk diri sendiri / situasi / benda** → `non_cyberbullying`.
  - "aku bego banget tadi", "server tolol", "goblok ni tutorial gaada yg work".

> Konsistensi wajib: bila "bacot vier / bacot pank" = `insult`, maka
> "bacot su / bacot [nama lain]" **juga** `insult`. Jangan beda perlakuan untuk pola yang sama.

---

## 6. Aturan Identitas (SARA) — selalu utama

Begitu ada **penanda identitas** (jawa, batak, cina, arab, kafir, kadrun, cebong,
banci, bencong, homo, lesbi, dll.) yang dipakai untuk **menyerang atau menolak**,
label = **`hate_speech`**, apa pun bentuk kalimatnya (hinaan maupun pengucilan).

Catatan: menyebut identitas secara **netral** ("aku orang jawa", "server anak Padang")
bukan hate_speech → nilai sesuai konteks (umumnya `non_cyberbullying`).

---

## 7. Contoh Multi-Sinyal yang Diselesaikan

| Pesan | Sinyal | Label benar | Alasan |
|---|---|---|---|
| "bacot lu terlalu nub untuk ikut dengan kami" | insult + exclusion | **exclusion** | Tak ada identitas/ancaman; inti = menolak gabung (Langkah 3 > insult) |
| "jawa tolool" | identitas + insult | **hate_speech** | Ada identitas (Langkah 2) |
| "jawa ga usah ikut" | identitas + exclusion | **hate_speech** | Pengucilan berbasis suku → identitas menang, **bukan** exclusion |
| "bacot lu kontol, gausah ikut²" | insult + exclusion | **exclusion** | Inti = pengucilan (exclusion > insult) |
| "bacot su" | insult (ke nama) | **insult** | Umpatan diarahkan ke orang |
| "server tolol lag mulu" | insult (ke benda) | **non_cyberbullying** | Sasaran benda (Langkah 0) |
| "mampus covid", "bunuh fatalis" | kata 'mati/bunuh' | **non_cyberbullying** | Bukan ancaman ke orang |

---

## 8. Kasus Sulit (pegangan cepat)

- **Banter akrab:** jelas bercanda & tak ada niat menyakiti → `non_cyberbullying`.
  Bila ragu bercanda vs menyerang → lihat konteks; tetap ragu → condong `non_cyberbullying`.
- **Umpatan tanpa sasaran:** "anjir/bangsat" meluapkan emosi sendiri → `non_cyberbullying`.
- **Sarkasme menyakiti:** sindiran jelas merendahkan target → kategori yang sesuai (umumnya `insult`).
- **Mengutip orang lain:** nilai dari maksud penulis, bukan kata yang dikutip.
- **Ambigu tanpa konteks:** tak bisa dipastikan → `non_cyberbullying`, catat sebagai ambigu.

---

## 9. Alur Teknis Melabeli

1. Buka berkas pelabelan (CSV) di Excel/Sheets/LibreOffice.
2. Baca kolom `teks`. Kolom `kata_terdeteksi` / `hasil_screening` hanya **petunjuk**, bukan jawaban.
3. Jalankan pesan lewat **Pohon Keputusan (bagian 2)** dari Langkah 0.
4. Isi kolom `label` dengan salah satu dari 6 kode (bagian 1).
5. Untuk konsistensi, sesekali cek ulang pola berulang (mis. semua "bacot + nama" harus sama).
