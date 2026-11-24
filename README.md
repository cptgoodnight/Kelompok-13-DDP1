# Rak-it! Pacil — Kelompok 13 DDP1-G

Sistem pelacak berkas & kertas kuis fisik Sekretariat Fasilkom UI berbasis **Python Flask** + JSON storage, dengan denah lemari rak `A1`–`E3` (Baris `A`–`E`, Kolom `1`–`3`), checklist mahasiswa dinilai untuk Asdos, notifikasi mahasiswa, dan integrasi SCELE/SSO UI.

## Struktur Modul (Pembagian 4 Anggota)

- `models.py` *(Anggota 1)* — Model data (`Student`, `ClassRoster`, `User`, `Envelope`, `QuizRecord`, `Notification`), koordinat rak `A1`–`E3`, rekomendasi loker paling kosong, dan statistik.
- `storage.py` *(Anggota 2)* — Penyimpanan lokal `data/store.json`, roster kelas, CRUD amplop/kertas lepas, query notifikasi, dan impor roster CSV SCELE.
- `auth.py`, `notifications.py`, `qr_utils.py`, `scele.py` *(Anggota 3)* — Login demo & CAS 2.0 SSO UI (`sso.ui.ac.id/cas2/`), sistem notifikasi modular (`Notifier`), generator QR kompartemen, dan klien Moodle Web Services SCELE (`scele.cs.ui.ac.id`).
- `app.py` & `templates/index.html` *(Anggota 4)* — Server Flask, REST API, deep link QR (`/slot/C2`), dan antarmuka web.

## Cara Menjalankan (Windows PowerShell)

1. Masuk ke folder proyek:
   ```powershell
   cd C:\Users\62812\OneDrive\Documents\UI\ddp1\proyek
   ```

2. Buat virtual environment dan pasang dependensi (cukup sekali saat setup awal):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\pip.exe install -r requirements.txt
   ```
   > Jika `python` mengarah ke alias Microsoft Store, gunakan path Python langsung (misal `C:\Users\<user>\AppData\Local\Python\pythoncore-3.14-64\python.exe -m venv .venv`).

3. Jalankan server Flask dari folder proyek:
   ```powershell
   .\.venv\Scripts\python.exe app.py
   ```
   > **Catatan PowerShell:** Selalu jalankan dari folder root proyek (`proyek`, bukan dari dalam `.venv\Scripts`) dan sertakan awalan `.\` agar PowerShell memakai Python di dalam `.venv`, bukan alias `python` dari Microsoft Store.

4. Buka di browser:
   - Halaman utama: `http://127.0.0.1:5000`
   - Deep link QR kompartemen (contoh loker `C2`): `http://127.0.0.1:5000/slot/C2`

## Akun Simulasi Cepat (Demo SSO UI)

- **Asdos:** `jonathan.tan` (DDP 1 — Kelas G, DDP 2 — Kelas C, SDA — Kelas Reguler) atau `nadia.khairunnisa` (Basdat, OS, Jarkom)
- **Mahasiswa:** `alya.zahra24` atau `muhammad.rafli24`

## Konfigurasi Opsional (Environment Variables)

- `ENABLE_REAL_SSO=1` — Menampilkan tombol login langsung ke SSO UI CAS 2.0 (`https://sso.ui.ac.id/cas2/`).
- `SCELE_BASE_URL` — Default `https://scele.cs.ui.ac.id`.
- `SCELE_WS_SERVICE` — Default `moodle_mobile_app`.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` — Mengaktifkan pengiriman email asli via `smtplib` (tanpa ini, email disimulasikan di log terminal).
- `NOTIFY_WEBHOOK_URL` — URL webhook Discord/Telegram untuk notifikasi.
