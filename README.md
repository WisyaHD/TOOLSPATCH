# JSON Corrector Tool

Alat ini digunakan untuk mengoreksi (encrypt/decrypt) nilai-nilai tertentu dalam file JSON berdasarkan key yang ditentukan. Alat ini menggunakan algoritma enkripsi sederhana untuk mengubah nilai string pada key yang dipilih.

## Fitur
- Mendukung enkripsi dan dekripsi nilai string pada key tertentu.
- Mendukung objek bersarang dan array.
- Membuat file JSON baru dengan hasil koreksi.
- Interface command-line sederhana.

## Persyaratan
- Node.js (versi 12 atau lebih baru)

## Instalasi
1. Pastikan Node.js terinstal di sistem Anda.
2. Clone atau download repository ini.
3. Jalankan `npm install` jika ada dependencies (dalam hal ini, tidak ada dependencies eksternal selain yang built-in).

## Cara Penggunaan

Jalankan perintah berikut di terminal:

```
node index.js <input.json> <keys> <encrypt|decrypt> <output.json>
```

### Parameter:
- `<input.json>`: Path ke file JSON asli yang ingin dikoreksi.
- `<keys>`: Daftar key yang ingin dikoreksi, dipisahkan dengan koma. Contoh: `nama_barang,kode_intern,tag_id`.
- `<encrypt|decrypt>`: Pilih tipe operasi:
  - `encrypt`: Mengenkripsi nilai-nilai pada key yang ditentukan.
  - `decrypt`: Mendekripsi nilai-nilai pada key yang ditentukan.
- `<output.json>`: Nama file JSON baru yang akan dibuat dengan hasil koreksi.

### Contoh Penggunaan:

1. **Dekripsi key `tag_id` dari file `db_tu.tm_barang.json` dan simpan ke `corrected.json`:**
   ```
   node index.js db_tu.tm_barang.json tag_id decrypt corrected.json
   ```

2. **Enkripsi beberapa key (`nama_barang` dan `kode_intern`) dari file `data.json` dan simpan ke `encrypted.json`:**
   ```
   node index.js data.json nama_barang,kode_intern encrypt encrypted.json
   ```

3. **Dekripsi semua key yang relevan dari file bersarang:**
   ```
   node index.js nested_data.json key1,key2,key3 decrypt output.json
   ```

### Catatan:
- Jika key tidak ditemukan atau nilai bukan string, alat akan melewatkannya.
- File output akan diformat dengan indentasi 2 spasi untuk kemudahan baca.
- Jika terjadi error (misalnya file tidak ditemukan atau JSON invalid), pesan error akan ditampilkan di terminal.

### Algoritma Enkripsi:
Alat ini menggunakan algoritma enkripsi sederhana berbasis XOR dengan key tetap "b3r4sput1h". Ini bukan enkripsi aman untuk data sensitif; gunakan hanya untuk keperluan internal.

### Troubleshooting:
- Pastikan path file benar dan file JSON valid.
- Jika key mengandung spasi atau karakter khusus, pastikan dipisahkan dengan koma tanpa spasi ekstra.
- Untuk objek bersarang, alat akan memproses secara rekursif.

Jika ada pertanyaan atau perlu penyesuaian, hubungi pengembang.
