# PBL-FastAPI-MachineLearning: Panduan Instalasi

## Langkah-Langkah Instalasi

1. **Instal Python (Versi 3.12)**  
   Pastikan Python versi **3.12** terinstal di perangkat lokal Anda. Jika belum, Anda dapat mengunduhnya dari situsnya Python.
   <li> Windows : https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe</li>
   <li> MacOS : https://www.python.org/ftp/python/3.12.7/python-3.12.7-macos11.pkg</li>

3. **Unduh File Model**  
   Unduh file model `.h5` yang dibutuhkan dari tautan berikut:  
   https://drive.google.com/file/d/1jYZ1oEWbjPc5OHQciIC3ICrTfabYTJt7/view?usp=sharing

4. **Pindahkan File Model**  
   Setelah mengunduh file `.h5`, pindahkan file tersebut ke dalam folder **Model** di direktori proyek Anda.

5. **Instal Dependencies**  
   Buka terminal atau command prompt di direktori proyek, lalu jalankan perintah berikut untuk menginstal semua dependensi yang diperlukan:  
   ```bash
   pip install -r requirements.txt
   ```

6. **Jalankan Proyek**  
   Setelah semua dependensi terinstal, jalankan aplikasi FastAPI menggunakan `uvicorn` dengan perintah berikut:  
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

7. **Selesai!**  
   🎉 Server FastAPI Anda sekarang berjalan di localhost! Selamat mencoba dan semoga sukses! 🥳
