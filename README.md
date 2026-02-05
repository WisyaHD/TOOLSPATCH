# TT Member Processing Tool

Modern web-based tool untuk memproses dan transform data TT Member dengan antarmuka yang user-friendly dan konfigurasi database yang mudah.

## 🚀 Features

### Database Configuration
- **UI-Based Configuration**: Konfigurasi MongoDB, database member, dan database jual langsung dari UI
- **Connection Testing**: Test koneksi MongoDB sebelum menyimpan konfigurasi
- **Auto-Save to .env**: Konfigurasi otomatis tersimpan di file .env
- **Real-time Config Update**: Perubahan konfigurasi langsung aktif tanpa restart server

### Data Processing
- **Patch Data**: Lookup dan update data dari tt_jual_detail berdasarkan no_faktur_jual, kode_barcode, atau berat
- **Transform Structure**: Transform struktur data Arjuna dari format lama ke format baru dengan information_transaction
- **Real-time Progress**: Monitor proses dengan progress bar dan status updates
- **File Management**: Upload dan kelola file JSON dengan mudah
- **Download Results**: Download hasil processing langsung dari browser

## 📋 Prerequisites

- Python 3.7+
- MongoDB connection (configured via UI or .env)
- Required Python packages (lihat requirements.txt)

## 🔧 Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Konfigurasi awal file `.env` jika ingin set secara manual:
```bash
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

**ATAU** langsung konfigurasi via UI setelah menjalankan aplikasi (Recommended)

## 🏃 Running the Application

1. Start the web server:
```bash
python3 app.py
```

2. Open browser dan akses:
```
http://localhost:5001
```

3. Server akan menampilkan:
```
================================================================================
🚀 TT Member Processing Tool
================================================================================
Server running at: http://localhost:5001
Press Ctrl+C to stop
================================================================================
```

## 🎯 Usage Guide

### 1. Database Configuration (FIRST TIME SETUP)

#### Via UI (Recommended):
1. Buka aplikasi di browser (`http://localhost:5001`)
2. Klik tab **"🔧 Database Configuration"**
3. Isi form konfigurasi:
   - **MongoDB Configuration**:
     - MongoDB URI (format: `mongodb://username:password@host:port/`)
     - Klik "Test Connection" untuk memastikan koneksi berhasil
   - **Database Member**:
     - Database Name (misal: `tmsambassg`)
     - Collection Name (default: `tt_member`)
   - **Database Jual**:
     - Database Name (misal: `tmsambassg`)
     - Collection Name (default: `tt_jual_detail`)
   - **Database Beli**:
     - Database Name (misal: `tmsambassg`)
     - Collection Name (default: `tt_beli_detail`)
     - Collection Hutang (default: `tt_hutang_detail`)
4. Klik **"💾 Save Database Configuration"**
5. Tunggu notifikasi "Configuration saved successfully"

#### Via .env File:
Buat atau edit file `.env`:
```env
MONGODB_URI=mongodb://username:password@host:port/database
DB_MEMBER=tmsambassg
DB_JUAL=tmsambassg
DB_BELI=tmsambassg
COLLECTION_TT_MEMBER=tt_member
COLLECTION_TT_JUAL_DETAIL=tt_jual_detail
COLLECTION_TT_BELI_DETAIL=tt_beli_detail
COLLECTION_TT_HUTANG_DETAIL=tt_hutang_detail
```

### 2. Data Processing

#### Patch Data:
1. Pindah ke tab **"🚀 Data Processing"**
2. Di section "Patch Data":
   - Pilih file JSON dari dropdown
   - Klik tombol **"🚀 Start Patch Process"**
   - Monitor progress bar dan status message
   - Download hasil jika proses selesai

#### Transform Structure:
1. Di section "Transform Structure":
   - Pilih file JSON dari dropdown
   - Klik tombol **"✨ Start Transform"**
   - Monitor progress bar
   - Download hasil transformasi

## 📁 Project Structure

```
script tt member/
├── app.py                          # Flask web application (dengan API config)
├── config.py                       # Configuration management
├── templates/
│   └── index.html                  # Web UI dengan tabs
├── patch_ultra_fast.py             # Script untuk patch data
├── transform_arjuna_structure.py   # Script untuk transform struktur
├── .env                            # Environment configuration (auto-updated via UI)
├── requirements.txt                # Python dependencies
├── uploads/                        # Uploaded files directory
├── outputs/                        # Processed files directory
└── README.md                       # Documentation
```

## 🎯 Features Detail

### Database Configuration Features
- ✅ **Test Connection**: Verifikasi koneksi MongoDB sebelum save
- ✅ **Auto-Save**: Konfigurasi tersimpan otomatis ke `.env`
- ✅ **Real-time Update**: Config langsung aktif tanpa restart
- ✅ **Database List**: Tampilkan list database yang tersedia setelah koneksi berhasil
- ✅ **Form Validation**: Validasi field yang wajib diisi

### Patch Data Features

**Proses Patch:**
- Lookup ke tt_jual_detail berdasarkan:
  1. no_faktur_jual (prioritas 1)
  2. kode_barcode dari deskripsi (prioritas 2)
  3. berat (prioritas 3)
- Update fields: nama_barang, kadar, kode_barcode, no_faktur, dll

### Transform Structure

1. Pilih file JSON dari dropdown "Transform Structure"
2. Klik tombol "Start Transform"
3. Tunggu proses selesai
4. Download hasil dari link yang muncul

**Proses Transform:**
- Convert dari format lama (flat structure) ke format baru
- Tambahkan information_transaction array
- Enrich data dari tt_jual_detail
- Update member.no_faktur_jual

## 🗄️ Database Mapping

Database yang didukung:

**HDP Group:**
- KMT → db_hdpkmt
- HGY → db_hdpayn_asli
- KM2 → db_hdpkmt2
- MKT → db_hdpmkt
- PGG → db_hdppgg
- PMG → db_hdppmg
- PMP, PML → db_hdppml
- HPM → db_hdppmr
- HPS → db_hdppst
- SAG → db_hdpsag
- HSL → db_hdphsl
- SAO → db_hdpsao
- SA → db_hdpsa
- SL → db_hdpsl
- PGN → db_hdppgn

**Arjuna Group:**
- ARJ, EAJ, JNK → db_arjnjtb
- RJN → db_arjnptr
- RJ2 → db_arjnptr2
- APT → db_arjnputri

## ⚡ Performance

- **Batch Lookup Strategy**: Query semua data dalam 1 query per database
- **In-Memory Caching**: Cache hasil lookup untuk processing cepat
- **Parallel Processing**: Background processing dengan threading

**Typical Performance:**
- 296,731 members: ~2.5 menit (patch)
- 853,430 members: ~20 menit (patch)
- 128,335 members: ~32 menit (transform)

## 🛠️ Development

### Adding New Database Mapping

Edit `patch_ultra_fast.py` dan `transform_arjuna_structure.py`:

```python
DB_MAPPING = {
    # ... existing mappings
    "NEW": os.getenv('DB_JUAL_NEW', 'db_new_database'),
}
```

Update `.env`:
```
DB_JUAL_NEW=db_new_database
```

### Customizing UI

Edit `templates/index.html` untuk mengubah tampilan web interface.

## 📊 Output Format

### Patched Data
```json
{
  "kategori": "B278C07EC8B1C1B57F",
  "information_transaction": [{
    "nama_barang": "A953AA7F93BC95B780BA53C18AB4BC",
    "kadar": 100,
    "kode_barcode": "00750119",
    "no_faktur": "KMT-FJ-20251225-0027"
  }]
}
```

### Transformed Data
```json
{
  "kode_member": "ARP0002889",
  "no_faktur_jual": "RJN-FJ-20251230-0061",
  "information_transaction": [{
    "nama_barang": "A381C654BAC9C5C78A8880B786BCB3B69489976BBD",
    "berat": 1.5,
    "kadar": 100,
    "kode_barcode": "00365479"
  }],
  "schema_version": 2
}
```

## 🐛 Troubleshooting

### Port already in use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
python3 app.py --port 8000
```

### MongoDB connection timeout
- Check MongoDB server availability
- Verify connection string in .env
- Check firewall settings

### File not found
- Pastikan file JSON ada di directory yang sama dengan app.py
- Check file permissions

## 📝 Notes

- Maximum file size: 500MB
- Supported format: JSON only
- Processing timeout: 1 hour per operation
- Results auto-saved dengan suffix `_patched` atau `_transformed`

## 🔒 Security

- File upload dengan validation
- Secure filename handling
- Process isolation dengan threading
- Max file size limit

## 📄 License

Internal use only - NSI Project

## 👥 Support

Untuk bantuan atau pertanyaan, hubungi tim development.
