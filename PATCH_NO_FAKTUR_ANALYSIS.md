# 🎯 Analisis & Solusi: No_Faktur_Jual Tidak Muncul

## ❌ MASALAH YANG DITEMUKAN

### 1. **Mismatch Kode_Toko dengan Database Mapping**
```
Data memiliki: kode_toko = "SBP"
Script mapping hanya mencakup: AN1-AN7
Hasil: Lookup tidak dilakukan untuk kode_toko "SBP"
```

**Status kode_toko di data:**
```json
{
  "kode_toko": "SBP",
  "information_transaction": [
    {
      "no_faktur": "-",  // ← Seharusnya diisi dari tt_jual_detail
      "kode_barcode": "A0320302",
      "no_faktur_jual": "-"  // ← Masih kosong
    }
  ]
}
```

---

### 2. **Query Filter Terlalu Ketat**
File: `patch_no_faktur_ultra_fast.py` (line 107-114)
```python
# ❌ MASALAH: Filter ini terlalu ketat
results = tt_jual_detail.find(
    {
        "kode_barcode": {"$in": batch}, 
        "no_faktur_jual": {"$ne": "-", "$exists": True}  # ← TERLALU KETAT!
    },
    ...
)
```

**Mengapa bermasalah:**
- Jika `no_faktur_jual` adalah "-" atau kosong di database, tidak akan di-retrieve
- Data yang sebenarnya ada di `no_faktur` tidak akan diambil
- Fallback value tidak dipertimbangkan

---

### 3. **Tidak Ada Fallback Mechanism**
Script saat ini:
- Jika `kode_toko` tidak ada di mapping → SKIP
- Jika barcode tidak ketemu di database → TIDAK CARI KE DATABASE LAIN
- Tidak ada recovery strategy

---

## ✅ SOLUSI

### **2 Script Baru yang Sudah Dibuat:**

#### **1. `patch_no_faktur_fixed.py`** (Rekomendasi Pertama)
**Perbaikan:**
- ✅ Tambah `'SBP': 'tmsambaskj'` ke db_mapping
- ✅ Relaksasi query: hapus filter `no_faktur_jual != "-"`
  ```python
  results = tt_jual_detail.find(
      {"kode_barcode": {"$in": batch}},  # ✅ Query lebih luas
      {...}
  )
  ```
- ✅ Fallback logic: gunakan `no_faktur_jual` OR `no_faktur`
  ```python
  no_faktur_value = doc.get('no_faktur_jual') or doc.get('no_faktur') or '-'
  ```
- ✅ Tracking field tambahan:
  - `lookup_source`: 'tt_jual_detail'
  - `lookup_db`: nama database yang digunakan

---

#### **2. `patch_no_faktur_aggressive.py`** (Untuk Kasus Ekstrim)
**Strategi dua-layer lookup:**

**Layer 1 (Primary):** Cari di database sesuai `kode_toko`
```python
if kode_toko in primary_cache and kode_barcode in primary_cache[kode_toko]:
    jual_data = primary_cache[kode_toko][kode_barcode]
    source = 'primary'
```

**Layer 2 (Fallback):** Jika tidak ketemu, cari di SEMUA database lain
```python
elif kode_barcode in fallback_cache:
    jual_data = fallback_cache[kode_barcode]
    source = 'fallback'
```

**Hasil:** Tracking di `lookup_source` menunjukkan dari mana data diambil
```json
"lookup_source": "tt_jual_detail (primary)" // atau (fallback)
"lookup_db": "tmsambaskj"  // database mana
```

---

## 📊 CARA MENGGUNAKAN

### **Opsi 1: FIXED Version (Standard)**
```bash
python3 patch_no_faktur_fixed.py \
    "uploads/sambas_pwj_pst.tt_member_transformed_4.json" \
    "uploads/sambas_pwj_pst.tt_member_transformed_4_no_faktur_FIXED.json"
```

**Output:**
```
[Step 1] Loading uploads/sambas_pwj_pst.tt_member_transformed_4.json...
✓ Loaded 1,234 records

[Step 2] Connecting to MongoDB...
  ✓ SBP → tmsambaskj
  
[Step 3] Collecting kode_barcode to lookup...
✓ Unique kode_toko in data: ['SBP']
✓ Kode_barcode need lookup per toko:
  - SBP (tmsambaskj): 856 unique

[Step 4] Building cache from tt_jual_detail...
  Processing SBP → tmsambaskj
    ✓ Cached 750 records

[Step 5] Patching data using cache...
  Processed: 1,234/1,234 records

✓ No_Faktur Updated:
  - Patched (dari '-'): 750
  - Nama_Barang Updated: 120
  - No_Faktur_Jual Added: 750
```

---

### **Opsi 2: AGGRESSIVE Version (Jika Ada Data Anomali)**
```bash
python3 patch_no_faktur_aggressive.py \
    "uploads/sambas_pwj_pst.tt_member_transformed_4.json" \
    "uploads/sambas_pwj_pst.tt_member_transformed_4_no_faktur_AGGRESSIVE.json"
```

**Output:**
```
[Step 5] Building fallback cache (searching all databases)...
  Barcodes not found in primary: 106

  Searching tmsambassg... → Found 45
  Searching tmsambaskj... → Found 0
  Searching tmsambasks... → Found 12
  Searching tmsambasmg... → Found 28
  ...

✓ No_Faktur Updated:
  - Primary cache: 750
  - Fallback cache: 85
  - TOTAL: 835
```

---

## 🔍 CEK HASILNYA

**Bandingkan hasil sebelum & sesudah:**

```bash
# Cek file original
python3 -c "
import json
with open('uploads/sambas_pwj_pst.tt_member_transformed_4.json') as f:
    data = json.load(f)
    trans = data[0]['information_transaction'][0]
    print('BEFORE:')
    print(f'  no_faktur: {trans.get(\"no_faktur\")}')
    print(f'  no_faktur_jual: {trans.get(\"no_faktur_jual\")}')
    print(f'  kode_barcode: {trans.get(\"kode_barcode\")}')
"

# Cek file setelah patching
python3 -c "
import json
with open('uploads/sambas_pwj_pst.tt_member_transformed_4_no_faktur_FIXED.json') as f:
    data = json.load(f)
    trans = data[0]['information_transaction'][0]
    print('AFTER:')
    print(f'  no_faktur: {trans.get(\"no_faktur\")}')
    print(f'  no_faktur_jual: {trans.get(\"no_faktur_jual\")}')
    print(f'  lookup_source: {trans.get(\"lookup_source\")}')
    print(f'  lookup_db: {trans.get(\"lookup_db\")}')
"
```

---

## 📋 RINGKASAN PERBAIKAN

| Aspek | Masalah Lama | Solusi FIXED | Solusi AGGRESSIVE |
|-------|-------------|------------|-------------------|
| **Kode_Toko Mapping** | Hanya AN1-AN7 | ✅ +SBP | ✅ +SBP |
| **Query Filter** | Ketat (`no_faktur_jual != "-"`) | ✅ Relaksed | ✅ Relaksed |
| **Fallback Logic** | Tidak ada | ✅ `no_faktur_jual` OR `no_faktur` | ✅ Two-layer lookup |
| **Multi-DB Search** | Tidak ada | ✅ Dalam database yang sesuai | ✅ Cross-database |
| **Tracking** | Minimal | ✅ `lookup_source`, `lookup_db` | ✅ Lengkap (primary/fallback) |
| **Performance** | - | ⚡ Lebih cepat | ⚠️ Lebih lambat |

---

## 🚀 REKOMENDASI

1. **Mulai dengan `patch_no_faktur_fixed.py`** - paling stable
2. **Jika coverage < 80%**, gunakan `patch_no_faktur_aggressive.py`
3. **Monitor `lookup_source` & `lookup_db`** untuk debugging
4. **Update `db_mapping` di semua script** jika ada kode_toko baru

---

## 📝 NEXT STEPS

1. ✅ Jalankan `patch_no_faktur_fixed.py`
2. Cek hasil dengan script di atas
3. Jika ada yg masih "-", gunakan aggressive version
4. Update data ke database atau aplikasi sesuai kebutuhan
