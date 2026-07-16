# -*- coding: utf-8 -*-
"""
inisialisasi_db.py
Isi database dari berkas CSV yang SUDAH ada (sekali jalan), memigrasi label
lama (Inggris) -> Indonesia, lalu melatih model final berlabel Indonesia dan
menyimpannya ke database (tabel artifacts).

Jalankan sekali:  python inisialisasi_db.py
Berguna agar aplikasi web langsung punya data & model saat pertama dibuka.
"""
import os
import sys
import json
import getpass
import pandas as pd
from sqlalchemy import URL

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import db
from lib.labels import ke_indonesia, KELAS
from lib.pemodelan import latih

FOLDER_OUT = "hasil"

# Default koneksi Supabase (Session pooler) — tekan Enter untuk memakai default.
HOST_DEFAULT = "aws-0-ap-southeast-2.pooler.supabase.com"
USER_DEFAULT = "postgres.jemackjxcjomdbpurqcf"


def pastikan_koneksi():
    """Siapkan koneksi database dengan AMAN:
    - Bila DATABASE_URL sudah diset di lingkungan, pakai itu.
    - Bila tidak, TANYA detail koneksi + sandi TERSEMBUNYI (getpass), lalu bangun
      URL via SQLAlchemy (otomatis meng-encode karakter spesial spt '@').
      Sandi tidak pernah tampil di layar / riwayat perintah.
    """
    if os.environ.get("DATABASE_URL"):
        print("Memakai DATABASE_URL dari lingkungan.")
        return
    print("=" * 60)
    print("SAMBUNG KE SUPABASE (Session pooler). Tekan Enter untuk default.")
    print("=" * 60)
    host = input(f"Host [{HOST_DEFAULT}]: ").strip() or HOST_DEFAULT
    user = input(f"User [{USER_DEFAULT}]: ").strip() or USER_DEFAULT
    pw = getpass.getpass("Password Supabase (ketik, TIDAK tampil): ")
    if not pw:
        print("Password kosong — batal. Jalankan lagi.")
        sys.exit(1)
    url = URL.create("postgresql+psycopg2", username=user, password=pw,
                     host=host, port=5432, database="postgres")
    # render_as_string(hide_password=False) -> sandi otomatis di-encode (@ -> %40)
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)


def main():
    pastikan_koneksi()

    # 1) clean_messages dari data_bersih.csv
    #    PRIVASI: 49rb pesan ASLI. Hanya diunggah bila SEED_RAW=1 (default: TIDAK).
    #    Tanpa ini, halaman Prediksi/Evaluasi/Pelatihan tetap jalan penuh.
    if os.environ.get("SEED_RAW") == "1":
        p = os.path.join(FOLDER_OUT, "data_bersih.csv")
        if os.path.exists(p):
            dfc = pd.read_csv(p, keep_default_na=False)
            db.simpan_df("clean_messages", dfc[["msg_id", "server", "author_anon", "teks"]])
            print(f"clean_messages : {len(dfc)} baris (SEED_RAW=1)")
    else:
        print("clean_messages : DILEWATI (privasi). Set SEED_RAW=1 utk mengunggah pesan mentah.")

    # 2) labeled_data dari dataset_berlabel.csv (migrasi label -> Indonesia)
    p = os.path.join(FOLDER_OUT, "dataset_berlabel.csv")
    dfl = pd.read_csv(p, keep_default_na=False)
    dfl.columns = [c.lstrip("﻿") for c in dfl.columns]  # buang BOM
    dfl["label"] = dfl["label"].apply(ke_indonesia)
    dfl = dfl[dfl["label"].isin(KELAS)].copy()
    for c in ["server", "author_anon"]:
        if c not in dfl.columns:
            dfl[c] = ""
    dfl["sumber"] = "migrasi_csv"
    db.simpan_df("labeled_data",
                 dfl[["msg_id", "server", "author_anon", "teks", "label", "sumber"]])
    print(f"labeled_data   : {len(dfl)} baris")
    print("distribusi     :", dfl["label"].value_counts().to_dict())

    # 3) latih model final (label Indonesia) -> simpan ke artifacts
    print("\nMelatih model (label Indonesia) ...")
    hasil = latih(dfl[["teks", "label"]], lapor=lambda m: print("  ", m))
    db.simpan_joblib("model_6.joblib", hasil["model_6"])
    db.simpan_joblib("model_biner.joblib", hasil["model_biner"])
    db.simpan_joblib("tfidf.joblib", hasil["tfidf"])
    db.simpan_artifact("metrik.json",
                       json.dumps(hasil["metrik"], ensure_ascii=False).encode("utf-8"))
    db.simpan_artifact("cm_6kelas.png", hasil["cm6_png"])
    db.simpan_artifact("cm_biner.png", hasil["cm2_png"])

    m = hasil["metrik"]
    print("\n== HASIL (label Indonesia) ==")
    print(f"6 kelas : akurasi {m['enam_kelas']['akurasi']:.3f} | "
          f"macro-F1 {m['enam_kelas']['macro_f1']:.3f} | "
          f"CV {m['cv_enam_kelas']['akurasi_mean']:.3f}±{m['cv_enam_kelas']['akurasi_std']:.3f}")
    print(f"biner   : akurasi {m['biner']['akurasi']:.3f} | "
          f"macro-F1 {m['biner']['macro_f1']:.3f} | baseline {m['biner']['baseline']:.3f} | "
          f"CV {m['cv_biner']['akurasi_mean']:.3f}±{m['cv_biner']['akurasi_std']:.3f}")
    _peta = {"sqlite": "SQLite (hasil/app.db)", "mysql": "MySQL/MariaDB (XAMPP)",
             "postgresql": "PostgreSQL (Supabase)"}
    _nama = db.get_engine().dialect.name
    print(f"\nDatabase siap: {_peta.get(_nama, _nama)}")


if __name__ == "__main__":
    main()
