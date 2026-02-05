# 🛒 Multiple Database Jual - User Guide

## Fitur Baru: Multiple Database Jual untuk Berbagai Cabang

Aplikasi sekarang mendukung konfigurasi **multiple database jual** untuk berbagai cabang/toko yang berbeda. Ini sangat berguna jika Anda memiliki:

- Multiple branches/cabang dengan database terpisah
- Multiple kode toko (AN1, AN2, AN3, dll)
- Database berbeda untuk setiap lokasi

---

## 📋 Cara Menggunakan

### 1. Buka Database Configuration

1. Akses aplikasi di browser: `http://localhost:5001`
2. Klik tab **"🔧 Database Configuration"**
3. Scroll ke section **"🛒 Database Jual (Multiple Branches)"**

### 2. Set Default Database Jual

Isi database jual default yang akan digunakan jika tidak ada mapping spesifik:

```
Default Database Name: tmsambassg
Collection Name: tt_jual_detail
```

### 3. Tambah Database Per Cabang

Di bagian **"Database Per Cabang/Toko"**, Anda bisa menambahkan database untuk setiap kode toko:

**Contoh:**
```
Kode Toko: AN1
Database Name: tmsambassg
[➕ Tambah]
```

Klik tombol **"➕ Tambah"** untuk menambahkan.

### 4. Tambah Multiple Cabang

Ulangi langkah 3 untuk setiap cabang:

| Kode Toko | Database Name |
|-----------|---------------|
| AN1 | tmsambassg |
| AN2 | tmsambaskj |
| AN3 | tmsambasks |
| AN4 | tmsambasmg |
| AN5 | tmsambassj2 |
| AN6 | tmsambaskk |
| AN7 | tmsambasbjg |

### 5. Hapus Cabang (Jika Perlu)

Untuk menghapus database cabang, klik tombol **"✕ Hapus"** di sebelah kanan item.

### 6. Simpan Konfigurasi

Klik tombol **"💾 Save Database Configuration"** untuk menyimpan semua perubahan.

---

## 💻 Hasil di File .env

Setelah disimpan, file `.env` Anda akan terlihat seperti ini:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://user:pass@host:27017/

# Database Names
DB_MEMBER=tmsambassg
DB_JUAL=tmsambassg
DB_BELI=tmsambassg

# Collections
COLLECTION_TT_MEMBER=tt_member
COLLECTION_TT_JUAL_DETAIL=tt_jual_detail
COLLECTION_TT_BELI_DETAIL=tt_beli_detail
COLLECTION_TT_HUTANG_DETAIL=tt_hutang_detail

# Database Jual per Cabang/Toko
DB_JUAL_AN1=tmsambassg
DB_JUAL_AN2=tmsambaskj
DB_JUAL_AN3=tmsambasks
DB_JUAL_AN4=tmsambasmg
DB_JUAL_AN5=tmsambassj2
DB_JUAL_AN6=tmsambaskk
DB_JUAL_AN7=tmsambasbjg
```

---

## 🔧 Cara Menggunakan di Code

### Mendapatkan Database Jual untuk Cabang Tertentu

```python
from config import Config

# Get database jual untuk cabang AN1
db_name_an1 = Config.get_db_jual_for_branch('AN1')
print(db_name_an1)  # Output: tmsambassg

# Get database jual untuk cabang AN2
db_name_an2 = Config.get_db_jual_for_branch('AN2')
print(db_name_an2)  # Output: tmsambaskj

# Jika branch tidak ditemukan, akan return default DB_JUAL
db_name_unknown = Config.get_db_jual_for_branch('XX99')
print(db_name_unknown)  # Output: tmsambassg (default)
```

### Mendapatkan Semua Database Jual

```python
from config import Config

# Get all branch databases
all_branches = Config.get_all_db_jual_branches()
print(all_branches)
# Output: {
#     'AN1': 'tmsambassg',
#     'AN2': 'tmsambaskj',
#     'AN3': 'tmsambasks',
#     ...
# }

# Loop through all branches
for branch_code, db_name in all_branches.items():
    print(f"Cabang {branch_code}: {db_name}")
```

### Menggunakan di Script Patch

```python
from config import Config
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(Config.MONGODB_URI)

# Misal kode_toko dari data member adalah 'AN2'
kode_toko = member_data.get('kode_toko', 'AN1')

# Get database name untuk kode_toko tersebut
db_jual_name = Config.get_db_jual_for_branch(kode_toko)

# Access the correct database
db_jual = client[db_jual_name]
tt_jual_detail = db_jual[Config.COLLECTION_TT_JUAL_DETAIL]

# Query data
result = tt_jual_detail.find_one({'no_faktur_jual': no_faktur})
```

---

## 📊 Use Case Examples

### Use Case 1: Patch dengan Multiple Database

Script akan otomatis lookup ke database yang sesuai dengan `kode_toko`:

```python
for member in members:
    kode_toko = member.get('kode_toko', 'AN1')
    
    # Automatic database selection based on kode_toko
    db_jual_name = Config.get_db_jual_for_branch(kode_toko)
    db_jual = client[db_jual_name]
    
    # Query tt_jual_detail from correct database
    jual_data = db_jual[Config.COLLECTION_TT_JUAL_DETAIL].find_one({
        'kode_member': member['kode_member']
    })
```

### Use Case 2: Agregasi dari Semua Cabang

```python
from config import Config

# Process all branches
all_branches = Config.get_all_db_jual_branches()
total_transactions = 0

for branch_code, db_name in all_branches.items():
    db = client[db_name]
    count = db[Config.COLLECTION_TT_JUAL_DETAIL].count_documents({})
    total_transactions += count
    print(f"Branch {branch_code}: {count} transactions")

print(f"Total: {total_transactions} transactions")
```

---

## 🎯 Best Practices

### 1. Naming Convention
Gunakan naming yang konsisten untuk kode toko:
- ✅ AN1, AN2, AN3 (recommended)
- ✅ CAB01, CAB02, CAB03
- ❌ Cabang1, toko-2, Branch_3 (inconsistent)

### 2. Default Database
Selalu set default database jual untuk fallback:
```python
db_name = Config.get_db_jual_for_branch(kode_toko)
# Jika kode_toko tidak ditemukan, akan return DB_JUAL default
```

### 3. Validasi Kode Toko
Sebelum query, pastikan kode_toko valid:
```python
all_branches = Config.get_all_db_jual_branches()
if kode_toko in all_branches:
    db_name = all_branches[kode_toko]
else:
    db_name = Config.DB_JUAL  # Use default
```

### 4. Testing
Test semua cabang setelah konfigurasi:
```python
for branch_code in ['AN1', 'AN2', 'AN3', 'AN4']:
    db_name = Config.get_db_jual_for_branch(branch_code)
    print(f"{branch_code} -> {db_name}")
```

---

## 🚨 Troubleshooting

### Issue: Database tidak muncul di UI setelah save

**Solusi:**
1. Refresh browser (Ctrl+F5 atau Cmd+Shift+R)
2. Cek file `.env` manual untuk memastikan tersimpan
3. Restart aplikasi

### Issue: Kode toko salah/tidak konsisten

**Solusi:**
1. Standardisasi format kode toko di database
2. Update mapping di UI
3. Gunakan uppercase untuk kode toko (AN1, bukan an1)

### Issue: Performance lambat dengan banyak database

**Solusi:**
1. Gunakan connection pooling MongoDB
2. Index yang tepat di setiap database
3. Cache hasil query jika memungkinkan

---

## 📈 Migration Guide

### Dari Single Database ke Multiple Database

**Before:**
```env
DB_JUAL=db_hdpayn_asli
```

**After:**
```env
DB_JUAL=tmsambassg  # Default
DB_JUAL_AN1=tmsambassg
DB_JUAL_AN2=tmsambaskj
DB_JUAL_AN3=tmsambasks
```

**Update Script:**
```python
# Old code
db_jual = client[Config.DB_JUAL]

# New code
kode_toko = member.get('kode_toko', 'AN1')
db_jual_name = Config.get_db_jual_for_branch(kode_toko)
db_jual = client[db_jual_name]
```

---

## ✅ Checklist Setup

- [ ] Identifikasi semua kode toko/cabang
- [ ] Mapping database untuk setiap kode toko
- [ ] Input konfigurasi via UI
- [ ] Test connection untuk semua database
- [ ] Save configuration
- [ ] Verify di file `.env`
- [ ] Update script untuk menggunakan `get_db_jual_for_branch()`
- [ ] Test dengan data sample dari berbagai cabang

---

## 🎉 Summary

Dengan fitur ini, Anda dapat:
- ✅ Manage multiple database jual dari UI
- ✅ Automatic database selection based on kode_toko
- ✅ Easy to add/remove branches
- ✅ Configuration saved to .env automatically
- ✅ Fallback to default database if branch not found

**Selamat menggunakan fitur Multiple Database Jual! 🚀**
