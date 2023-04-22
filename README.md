# unpam-elearning-detector

Anda kesal karena dosen gak ngasih tau ketika E-learing muncul? ini jawabannya.

Program ini akan mendeteksi kalo ada elearning yang belum selesai, berikut adalah cara penggunaannya:

1. Buka file `.env.template` terlebih dahulu
2. Edit variable yang ada didalam file tersebut dengan data kamu
3. Lalu save ulang file tersebut dengan nama `.env`
4. Install modul yang dibutuhkan dengan command ini ```pip install -r requirement.txt```
5. Lalu jalankan `main.py` dengan command ini ```python main.py```

Setelah berjalan mungkin akan membutuhkan waktu `1 - 2 menit` untuk mengeceknya, setelah selesai program ini akan memberikan sebuah list yang berisikan tuple yang seperti ini ```[(" nama_matkul ", " indeks_forum ", " link_forum ")]```

Kalo pengen mengubah `output` kamu bisa mengecek kedalam file `main.py`

Kamu bisa menggunakan kode ini untuk otomaton yang nantinya bisa memberikan notifikasi ke kamu, tapi itu perlu tahapan lagi.
