#!/usr/bin/env python3
"""Test langsung ke database untuk verify data"""
import json
from pymongo import ReadPreference
from config import Config
from dotenv import load_dotenv
import os

load_dotenv()

# Database mapping dari .env
db_mapping = {
    'SBP': os.getenv('DB_JUAL_SBP', 'sambas_pwj_cb1'),
    'SBS': os.getenv('DB_JUAL_SBS', 'sambas_pwj_wts'),
    'SDR': os.getenv('DB_JUAL_SDR', 'db_tmsdrd'),
    'SPP': os.getenv('DB_JUAL_SPP', 'sambas_pwj_pst'),
    'SPW': os.getenv('DB_JUAL_SPW', 'sambas_pwj_pwj'),
    'SS2': os.getenv('DB_JUAL_SS2', 'db_sambasbelik2'),
}

print(f"\n{'='*70}")
print("TEST DATABASE LOOKUP")
print(f"{'='*70}\n")

# Load 1 sample dari JSON
json_file = 'uploads/sambas_pwj_pst.tt_member_transformed_4.json'
with open(json_file, 'r') as f:
    data = json.load(f)

# Ambil 5 sample yang no_faktur masih "-"
samples = []
for member in data[:1000]:  # Check first 1000 records
    if len(samples) >= 5:
        break
    kode_toko = member.get('kode_toko', '')
    if 'information_transaction' in member:
        for trans in member['information_transaction']:
            if trans.get('no_faktur') == '-':
                kode_barcode = trans.get('kode_barcode')
                if kode_barcode and kode_barcode != '-':
                    samples.append({
                        'kode_toko': kode_toko,
                        'kode_barcode': kode_barcode,
                        'nama_barang': trans.get('nama_barang', '-')
                    })
                    if len(samples) >= 5:
                        break

print(f"Testing {len(samples)} samples from JSON:\n")

# Connect dan test
try:
    client = Config.get_mongodb_client()
    
    for i, sample in enumerate(samples, 1):
        kode_toko = sample['kode_toko']
        kode_barcode = sample['kode_barcode']
        db_name = db_mapping.get(kode_toko, 'sambas_pwj_pst')
        
        print(f"Sample {i}:")
        print(f"  Kode Toko: {kode_toko}")
        print(f"  Kode Barcode: {kode_barcode}")
        print(f"  Database: {db_name}")
        
        # Query ke database
        db = client[db_name]
        
        # Check total records di tt_jual_detail
        total_count = db['tt_jual_detail'].count_documents({})
        print(f"  Total records in {db_name}.tt_jual_detail: {total_count:,}")
        
        # Search exact barcode
        result = db['tt_jual_detail'].find_one(
            {'kode_barcode': kode_barcode},
            {'kode_barcode': 1, 'no_faktur': 1, 'no_faktur_jual': 1, 'nama_barang': 1}
        )
        
        if result:
            print(f"  ✓ FOUND!")
            print(f"    - no_faktur: {result.get('no_faktur', '-')}")
            print(f"    - no_faktur_jual: {result.get('no_faktur_jual', '-')}")
            print(f"    - nama_barang: {result.get('nama_barang', '-')}")
        else:
            print(f"  ✗ NOT FOUND")
            
            # Try fuzzy search (first 5 chars)
            prefix = kode_barcode[:5] if len(kode_barcode) >= 5 else kode_barcode
            similar = db['tt_jual_detail'].find_one(
                {'kode_barcode': {'$regex': f'^{prefix}'}},
                {'kode_barcode': 1}
            )
            
            if similar:
                print(f"    ⚠ Similar barcode found: {similar.get('kode_barcode')}")
            else:
                print(f"    ⚠ No similar barcode either")
                
                # Show sample barcodes from this database
                print(f"    Sample barcodes in {db_name}:")
                samples_db = db['tt_jual_detail'].find({}, {'kode_barcode': 1}).limit(5)
                for s in samples_db:
                    print(f"      - {s.get('kode_barcode')}")
        
        print()
    
    client.close()
    
    print(f"{'='*70}")
    print("CONCLUSION:")
    print(f"{'='*70}")
    print("""
Jika barcode NOT FOUND:
  → Data tidak ada di database tt_jual_detail
  → no_faktur TIDAK BISA diisi dari database
  → Kemungkinan:
    1. Data belum di-sync ke tt_jual_detail
    2. Barcode format berbeda (A0320302 vs A032-0302)
    3. Data ada di collection lain (tt_jual, bukan tt_jual_detail)
    
Solusi:
  1. Check collection lain: tt_jual, tt_transaksi, dll
  2. Check format barcode di database vs JSON
  3. Import data tt_jual_detail yang hilang
""")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
