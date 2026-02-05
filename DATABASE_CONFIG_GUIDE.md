# Database Configuration Guide

## 📚 Panduan Konfigurasi Database

### 1. Memahami Struktur Konfigurasi

Aplikasi ini menggunakan 3 database utama:

#### Database Member
- **Fungsi**: Menyimpan data member/pelanggan
- **Collection**: `tt_member`
- **Fields penting**: 
  - `kode_member`
  - `nama_member`
  - `alamat`
  - `telepon`
  - dll.

#### Database Jual (Penjualan)
- **Fungsi**: Menyimpan detail transaksi penjualan
- **Collection**: `tt_jual_detail`
- **Fields penting**:
  - `no_faktur_jual`
  - `kode_barcode`
  - `nama_barang`
  - `kode_member`
  - dll.

#### Database Beli (Pembelian)
- **Fungsi**: Menyimpan detail transaksi pembelian
- **Collections**: 
  - `tt_beli_detail` (detail pembelian)
  - `tt_hutang_detail` (detail hutang)

---

## 🔧 Cara Konfigurasi

### Metode 1: Via Web UI (Recommended)

1. **Buka aplikasi** di browser (`http://localhost:5001`)

2. **Klik tab "Database Configuration"** (🔧)

3. **MongoDB Configuration**:
   ```
   MongoDB URI: mongodb://username:password@host:port/database
   ```
   - Ganti `username` dan `password` dengan kredensial MongoDB Anda
   - Ganti `host:port` dengan alamat server MongoDB
   - Contoh: `mongodb://admin:pass123@localhost:27017/`
   - Untuk replica set: `mongodb://user:pass@host1:27017,host2:27017,host3:27017/db?replicaSet=rs0`

4. **Test Connection**:
   - Klik tombol "🔌 Test Connection"
   - Jika berhasil, akan muncul list database yang tersedia
   - Jika gagal, periksa kembali URI dan pastikan MongoDB running

5. **Database Member**:
   ```
   Database Name: tmsambassg
   Collection Name: tt_member
   ```
   - Sesuaikan dengan nama database dan collection Anda

6. **Database Jual**:
   ```
   Database Name: tmsambassg
   Collection Name: tt_jual_detail
   ```
   - Bisa sama atau berbeda dengan Database Member

7. **Database Beli**:
   ```
   Database Name: tmsambassg
   Collection Name: tt_beli_detail
   Collection Hutang: tt_hutang_detail
   ```

8. **Simpan Konfigurasi**:
   - Klik tombol "💾 Save Database Configuration"
   - Tunggu notifikasi "Configuration saved successfully"
   - Konfigurasi akan tersimpan di file `.env`

### Metode 2: Edit File .env Manual

1. Buat atau edit file `.env` di root project:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://username:password@host:port/database

# Database Names
DB_MEMBER=tmsambassg
DB_JUAL=tmsambassg
DB_BELI=tmsambassg

# Collections
COLLECTION_TT_MEMBER=tt_member
COLLECTION_TT_JUAL_DETAIL=tt_jual_detail
COLLECTION_TT_BELI_DETAIL=tt_beli_detail
COLLECTION_TT_HUTANG_DETAIL=tt_hutang_detail
```

2. Restart aplikasi jika sedang berjalan

---

## 🌐 MongoDB URI Format

### Local MongoDB:
```
mongodb://localhost:27017/
```

### MongoDB dengan Authentication:
```
mongodb://username:password@localhost:27017/
```

### MongoDB Replica Set:
```
mongodb://user:pass@host1:27017,host2:27017,host3:27017/database?replicaSet=rs0&authSource=admin
```

### MongoDB Atlas (Cloud):
```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/database?retryWrites=true&w=majority
```

### Advanced Options:
```
mongodb://user:pass@host:port/db?authSource=admin&replicaSet=rs0&readPreference=secondaryPreferred&serverSelectionTimeoutMS=30000&connectTimeoutMS=20000&socketTimeoutMS=120000&retryWrites=true&w=majority&maxPoolSize=50
```

**Parameters penting:**
- `authSource`: Database untuk autentikasi (biasanya `admin`)
- `replicaSet`: Nama replica set
- `readPreference`: Preferensi pembacaan (`primary`, `secondary`, `secondaryPreferred`)
- `serverSelectionTimeoutMS`: Timeout untuk memilih server (ms)
- `connectTimeoutMS`: Timeout koneksi (ms)
- `socketTimeoutMS`: Timeout socket (ms)
- `maxPoolSize`: Maksimum connection pool

---

## ✅ Validasi Konfigurasi

### 1. Test Connection
Gunakan fitur "Test Connection" di UI untuk memastikan:
- MongoDB dapat diakses
- Username/password benar
- Network tidak ada masalah
- Database yang tersedia

### 2. Cek File .env
Pastikan file `.env` berisi semua konfigurasi yang diperlukan:
```bash
cat .env
```

### 3. Test di Python
```python
from config import Config
client = Config.get_mongodb_client()
print(client.list_database_names())
```

---

## 🚨 Troubleshooting

### Error: "Connection failed"
**Penyebab**:
- MongoDB tidak running
- URI salah
- Firewall memblokir koneksi
- Kredensial salah

**Solusi**:
1. Pastikan MongoDB running: `sudo systemctl status mongod`
2. Cek URI format
3. Test koneksi manual: `mongo "mongodb://host:port"`
4. Periksa firewall: `sudo ufw status`

### Error: "Authentication failed"
**Penyebab**:
- Username/password salah
- authSource salah
- User tidak memiliki privilege

**Solusi**:
1. Cek kredensial
2. Tambahkan `?authSource=admin` di URI
3. Buat user dengan privilege yang tepat:
```javascript
use admin
db.createUser({
  user: "username",
  pwd: "password",
  roles: ["readWrite", "dbAdmin"]
})
```

### Error: "Connection timeout"
**Penyebab**:
- Server MongoDB tidak dapat dijangkau
- Network lambat
- Replica set config salah

**Solusi**:
1. Tingkatkan timeout di URI:
   ```
   ?serverSelectionTimeoutMS=30000&connectTimeoutMS=20000
   ```
2. Cek network: `ping host`
3. Cek replica set status

### Error: "Database not found"
**Penyebab**:
- Nama database salah
- Database belum dibuat

**Solusi**:
1. Cek available databases setelah test connection
2. Gunakan nama database yang tepat
3. Buat database jika perlu

---

## 💡 Tips & Best Practices

### 1. Keamanan
- ❌ Jangan commit file `.env` ke Git
- ✅ Gunakan `.gitignore` untuk exclude `.env`
- ✅ Gunakan environment variables di production
- ✅ Gunakan strong password untuk MongoDB

### 2. Performance
- ✅ Gunakan `readPreference=secondaryPreferred` untuk replica set
- ✅ Set `maxPoolSize` sesuai kebutuhan
- ✅ Gunakan index di MongoDB untuk query cepat

### 3. Reliability
- ✅ Gunakan replica set untuk high availability
- ✅ Set timeout yang wajar
- ✅ Enable `retryWrites=true`

### 4. Development vs Production
**Development**:
```env
MONGODB_URI=mongodb://localhost:27017/
```

**Production**:
```env
MONGODB_URI=mongodb://user:pass@server1:27017,server2:27017,server3:27017/db?replicaSet=rs0&authSource=admin
```

---

## 📖 Contoh Konfigurasi

### Single Server (Development)
```env
MONGODB_URI=mongodb://localhost:27017/
DB_MEMBER=test_db
DB_JUAL=test_db
DB_BELI=test_db
```

### Replica Set (Production)
```env
MONGODB_URI=mongodb://nsi:CPJQhiZ8x8k5@103.93.130.182:27017,103.235.75.134:27017,157.66.35.67:27017/db_hdpayn_asli?authSource=admin&replicaSet=rs0&readPreference=secondaryPreferred&serverSelectionTimeoutMS=30000&connectTimeoutMS=20000&socketTimeoutMS=120000&retryWrites=true&w=majority&maxPoolSize=50
DB_MEMBER=tmsambassg
DB_JUAL=tmsambassg
DB_BELI=tmsambassg
```

### Multiple Databases per Branch
```env
MONGODB_URI=mongodb://user:pass@host:27017/
DB_MEMBER=tmsambassg
DB_JUAL_AN1=tmsambassg
DB_JUAL_AN2=tmsambaskj
DB_JUAL_AN3=tmsambasks
DB_JUAL_AN4=tmsambasmg
```

---

## 🔄 Update Konfigurasi

Jika perlu mengubah konfigurasi:

1. **Via UI**: 
   - Buka tab "Database Configuration"
   - Edit field yang perlu diubah
   - Klik "Save Database Configuration"

2. **Via .env**:
   - Edit file `.env`
   - Restart aplikasi

**Note**: Perubahan via UI akan langsung aktif tanpa restart, tapi disarankan restart untuk memastikan semua module menggunakan config terbaru.

---

## 📞 Support

Jika masih ada masalah, hubungi tim development atau cek dokumentasi MongoDB:
- MongoDB Docs: https://docs.mongodb.com/
- PyMongo Docs: https://pymongo.readthedocs.io/
