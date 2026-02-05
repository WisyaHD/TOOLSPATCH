# 🚀 Quick Start Guide - TT Member Patching Tool

## Mulai dalam 5 Menit!

### Step 1: Install & Run (2 menit)

```bash
# 1. Masuk ke folder project
cd "script tt member"

# 2. Install dependencies (jika belum)
pip install -r requirements.txt

# 3. Jalankan aplikasi
python3 app.py
```

✅ Server akan running di: **http://localhost:5001**

---

### Step 2: Konfigurasi Database (2 menit)

1. **Buka browser** → http://localhost:5001

2. **Klik tab** → 🔧 **Database Configuration**

3. **Isi MongoDB URI**:
   ```
   mongodb://username:password@host:port/
   ```
   
4. **Klik** → 🔌 **Test Connection**
   - ✅ Jika berhasil, akan muncul list database
   - ❌ Jika gagal, cek kembali URI Anda

5. **Isi Database Names**:
   - **Database Member**: `tmsambassg` (atau nama DB Anda)
   - **Database Jual**: `tmsambassg` (atau nama DB Anda)
   - **Database Beli**: `tmsambassg` (atau nama DB Anda)

6. **Isi Collection Names** (biasanya default sudah benar):
   - Collection Member: `tt_member`
   - Collection Jual: `tt_jual_detail`
   - Collection Beli: `tt_beli_detail`
   - Collection Hutang: `tt_hutang_detail`

7. **Klik** → 💾 **Save Database Configuration**

✅ Konfigurasi tersimpan!

---

### Step 3: Process Data (1 menit)

1. **Klik tab** → 🚀 **Data Processing**

2. **Untuk Patch Data**:
   - Pilih file JSON dari dropdown
   - Klik **"🚀 Start Patch Process"**
   - Tunggu progress bar selesai
   - Download hasilnya

3. **Untuk Transform Data**:
   - Pilih file JSON dari dropdown
   - Klik **"✨ Start Transform"**
   - Tunggu progress bar selesai
   - Download hasilnya

✅ Selesai!

---

## 📋 Checklist Setup

- [ ] Python 3.7+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] MongoDB running dan dapat diakses
- [ ] MongoDB URI sudah benar
- [ ] Database names sudah dikonfigurasi
- [ ] Test connection berhasil
- [ ] Konfigurasi sudah disimpan
- [ ] File JSON sudah siap untuk diprocess

---

## ⚡ Tips Cepat

### MongoDB URI Quick Reference:

**Local**:
```
mongodb://localhost:27017/
```

**With Authentication**:
```
mongodb://username:password@host:27017/
```

**Replica Set**:
```
mongodb://user:pass@host1:27017,host2:27017,host3:27017/db?replicaSet=rs0&authSource=admin
```

---

## 🆘 Quick Troubleshooting

### Server tidak start?
```bash
# Cek apakah port 5001 sudah digunakan
lsof -i :5001

# Atau gunakan port lain, edit app.py:
# app.run(debug=True, host='0.0.0.0', port=5002)
```

### Connection failed?
1. ✅ Cek MongoDB running: `sudo systemctl status mongod`
2. ✅ Cek firewall
3. ✅ Test manual: `mongo "mongodb://your-uri"`

### Authentication failed?
1. ✅ Cek username/password
2. ✅ Tambahkan `?authSource=admin` di URI

---

## 📺 Visual Guide

### Tab 1: Database Configuration
```
┌─────────────────────────────────────────┐
│ 🗄️ MongoDB Configuration              │
│                                         │
│ MongoDB URI: [___________________]     │
│ [🔌 Test Connection]                   │
│ ✅ Connected! Databases: db1, db2...   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 👥 Database Member                     │
│ Database Name: [tmsambassg]            │
│ Collection: [tt_member]                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🛒 Database Jual                       │
│ Database Name: [tmsambassg]            │
│ Collection: [tt_jual_detail]           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ [💾 Save Database Configuration]       │
└─────────────────────────────────────────┘
```

### Tab 2: Data Processing
```
┌─────────────────────────────────────────┐
│ 🔧 Patch Data                          │
│ Select JSON File: [▼ file.json]       │
│ [🚀 Start Patch Process]               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📊 Processing Status                   │
│ Progress: [████████░░] 80%             │
│ Status: Processing data...              │
└─────────────────────────────────────────┘
```

---

## 🎯 Common Workflows

### Workflow 1: First Time Setup
```
1. Install → 2. Run → 3. Configure DB → 4. Test Connection → 5. Save → 6. Process Data
```

### Workflow 2: Daily Usage
```
1. Run → 2. Select File → 3. Process → 4. Download
```

### Workflow 3: Change Database
```
1. Open UI → 2. DB Config Tab → 3. Edit Settings → 4. Test → 5. Save
```

---

## 📱 Access From Other Devices

Server running di: `http://0.0.0.0:5001`

Bisa diakses dari:
- **Local**: http://localhost:5001
- **Network**: http://192.168.1.X:5001 (ganti X dengan IP Anda)
- **Other devices**: http://YOUR_IP:5001

Check your IP:
```bash
# macOS/Linux
ifconfig | grep inet

# Windows
ipconfig
```

---

## 🎉 You're Ready!

Aplikasi Anda sekarang sudah:
- ✅ Running dengan UI yang user-friendly
- ✅ Configured untuk MongoDB
- ✅ Siap untuk process data
- ✅ Dapat diakses dari browser

**Happy Processing! 🚀**

---

## 📚 Need More Help?

- **Configuration Details**: Lihat `DATABASE_CONFIG_GUIDE.md`
- **Full Documentation**: Lihat `README.md`
- **Error Solutions**: Check Troubleshooting section di documentation
