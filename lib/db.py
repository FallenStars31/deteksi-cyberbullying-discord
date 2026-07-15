# -*- coding: utf-8 -*-
"""
lib/db.py
Lapisan database (SQLAlchemy). SATU sumber koneksi untuk seluruh aplikasi.

- LOKAL (membangun & mencoba): SQLite di `hasil/app.db` (bawaan Python, tanpa
  server). Otomatis dipakai bila tak ada konfigurasi Secrets.
- PRODUKSI (Streamlit Cloud): Postgres/Supabase. Isi di `.streamlit/secrets.toml`
  atau Streamlit Cloud → Settings → Secrets:

      [db]
      url = "postgresql+psycopg2://USER:PASSWORD@HOST:5432/postgres"

  Kode TIDAK berubah; cukup connection string.

Tabel:
  - clean_messages : hasil pembersihan (msg_id, server, author_anon, teks)
  - candidates     : kandidat hasil penyaringan utk dilabeli
  - labeled_data   : data final berlabel (ground truth)
  - artifacts      : berkas biner (model .joblib, metrik.json, gambar) sbg BLOB
"""

import os
import io
import datetime as _dt
import pandas as pd
from sqlalchemy import (create_engine, text, MetaData, Table, Column,
                        String, LargeBinary)

FOLDER_OUT = "hasil"
_SQLITE_PATH = os.path.join(FOLDER_OUT, "app.db")

_engine = None  # cache proses


def _db_url() -> str:
    """Sumber koneksi, urut prioritas:
      1. Variabel lingkungan DATABASE_URL (untuk skrip di luar Streamlit,
         mis. seeding Supabase:  DATABASE_URL="postgresql+psycopg2://..." python inisialisasi_db.py)
      2. Streamlit Secrets [db].url (saat aplikasi berjalan di Streamlit Cloud)
      3. SQLite lokal hasil/app.db (default untuk membangun & mencoba)
    """
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    try:
        import streamlit as st  # opsional: modul ini bisa dipakai di luar Streamlit
        if "db" in st.secrets and st.secrets["db"].get("url"):
            return st.secrets["db"]["url"]
    except Exception:
        pass
    os.makedirs(FOLDER_OUT, exist_ok=True)
    return f"sqlite:///{_SQLITE_PATH}"


def get_engine():
    global _engine
    if _engine is None:
        url = _db_url()
        # SQLite perlu opsi ini agar aman dipakai lintas-thread Streamlit.
        kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
        _engine = create_engine(url, future=True, **kwargs)
        _init(_engine)
    return _engine


def is_sqlite() -> bool:
    return _db_url().startswith("sqlite")


_meta = MetaData()
# LargeBinary -> otomatis jadi BLOB di SQLite & BYTEA di Postgres/Supabase
# (portabel lintas basis data). Tabel dataframe lain dibuat oleh pandas.to_sql.
_artifacts = Table(
    "artifacts", _meta,
    Column("nama", String, primary_key=True),
    Column("data", LargeBinary),
    Column("updated_at", String),
)


def _init(engine):
    _meta.create_all(engine)


# ---------------------------------------------------------------- DataFrame API
def simpan_df(nama_tabel: str, df: pd.DataFrame, mode: str = "replace"):
    """Simpan DataFrame ke tabel. mode: 'replace' (ganti) / 'append' (tambah)."""
    df.to_sql(nama_tabel, get_engine(), if_exists=mode, index=False)


def muat_df(nama_tabel: str) -> pd.DataFrame:
    """Baca seluruh tabel jadi DataFrame. Kosong bila tabel belum ada."""
    try:
        return pd.read_sql_table(nama_tabel, get_engine())
    except Exception:
        return pd.DataFrame()


def ada_tabel(nama_tabel: str) -> bool:
    from sqlalchemy import inspect
    return inspect(get_engine()).has_table(nama_tabel)


def jumlah_baris(nama_tabel: str) -> int:
    if not ada_tabel(nama_tabel):
        return 0
    with get_engine().connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {nama_tabel}")).scalar() or 0)


def hapus_tabel(nama_tabel: str):
    with get_engine().begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {nama_tabel}"))


# ---------------------------------------------------------------- Artifact API
def simpan_artifact(nama: str, data: bytes):
    """Simpan berkas biner (model/metrik/gambar) ke tabel artifacts."""
    now = _dt.datetime.now().isoformat(timespec="seconds")
    with get_engine().begin() as conn:
        # UPSERT sederhana: hapus lalu masukkan (portable SQLite & Postgres).
        conn.execute(text("DELETE FROM artifacts WHERE nama=:n"), {"n": nama})
        conn.execute(text("INSERT INTO artifacts (nama, data, updated_at) VALUES (:n,:d,:t)"),
                     {"n": nama, "d": data, "t": now})


def muat_artifact(nama: str):
    """Kembalikan bytes berkas, atau None bila tak ada."""
    with get_engine().connect() as conn:
        row = conn.execute(text("SELECT data FROM artifacts WHERE nama=:n"), {"n": nama}).fetchone()
    if not row:
        return None
    d = row[0]
    return bytes(d) if d is not None else None


def ada_artifact(nama: str) -> bool:
    return muat_artifact(nama) is not None


def simpan_joblib(nama: str, obj):
    """Serialisasi objek Python (model/vectorizer) via joblib -> artifacts."""
    import joblib
    buf = io.BytesIO()
    joblib.dump(obj, buf)
    simpan_artifact(nama, buf.getvalue())


def muat_joblib(nama: str):
    import joblib
    b = muat_artifact(nama)
    if b is None:
        return None
    return joblib.load(io.BytesIO(b))
