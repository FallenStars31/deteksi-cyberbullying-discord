# Panduan Deploy Online (Supabase + Streamlit Cloud)

Agar aplikasi bisa diakses lewat internet. Kode sudah disiapkan; langkah di bawah
adalah bagian yang **harus Anda kerjakan sendiri** (buat akun & kredensial).

> ⚠️ **Jangan pernah menempelkan kata sandi database ke chat AI.** Isi sendiri
> di berkas `secrets.toml` / Streamlit Cloud.

---

## Langkah 1 — Buat database Supabase (gratis)
1. Daftar di **https://supabase.com** → **New project**.
2. Pilih region terdekat (mis. **Southeast Asia / Singapore**).
3. Buat **Database Password** yang kuat — **catat**, dipakai di Langkah 2.
4. Tunggu project selesai dibuat (~2 menit).

## Langkah 2 — Ambil connection string
1. Supabase → **Project Settings → Database → Connection string**.
2. Pilih tab **URI**, gunakan mode **Session pooler** (kompatibel Streamlit Cloud).
3. Salin URL-nya, lalu **ubah awalannya** dari `postgresql://` menjadi
   `postgresql+psycopg2://`, dan ganti `[YOUR-PASSWORD]` dengan sandi Langkah 1.
   Contoh hasil akhir:
   ```
   postgresql+psycopg2://postgres.abcdefgh:SANDI_ANDA@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```
   > Bila sandi mengandung karakter `@ : / #`, ubah dulu jadi bentuk URL-encoded.

## Langkah 3 — Isi data & model ke Supabase (dari komputer Anda)
Jalankan sekali (ganti URL dengan milik Anda). Ini mengunggah data bersih, data
berlabel, dan melatih + menyimpan model ke Supabase:
```bash
# Windows (PowerShell)
$env:DATABASE_URL="postgresql+psycopg2://...isi Anda..."; python inisialisasi_db.py

# Git Bash / Linux / Mac
DATABASE_URL="postgresql+psycopg2://...isi Anda..." python inisialisasi_db.py
```
Bila muncul ringkasan angka & "Database siap: Postgres/Supabase" → berhasil.

> 🔒 **Privasi:** langkah ini menaruh **pesan asli** di cloud. Bila tak ingin
> mengunggah seluruh 49rb pesan mentah, beri tahu saya — bisa dibuat agar hanya
> data berlabel + model yang diunggah.

## Langkah 4 — Push kode ke GitHub
Pastikan `.streamlit/secrets.toml` **tidak** ikut (sudah di `.gitignore`).
Repo cukup berisi kode + `kamus/`; data mentah & `app.db` tidak diunggah.

## Langkah 5 — Deploy di Streamlit Community Cloud
1. Buka **https://share.streamlit.io** → **New app** → pilih repo & branch.
2. **Main file path:** `Beranda.py`
3. Buka **Advanced settings → Secrets**, tempel:
   ```toml
   [db]
   url = "postgresql+psycopg2://...isi Anda..."
   ```
4. **Deploy.** Streamlit memasang `requirements.txt` lalu menjalankan app.

## Langkah 6 — Lindungi akses (disarankan)
Aplikasi Streamlit Cloud **publik** secara bawaan → siapa pun bisa melihat isi
pesan di halaman Penyaringan/Pelabelan. Pilihan pengamanan:
- **Batasi viewer**: Streamlit Cloud → App settings → Sharing → daftar email yang boleh.
- **Gerbang kata sandi** di dalam aplikasi (saya bisa tambahkan bila diminta).

---

### Kembali ke lokal (SQLite)
Hapus/rename `.streamlit/secrets.toml` dan jangan set `DATABASE_URL` →
aplikasi otomatis memakai `hasil/app.db` lagi.
