import json
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGODB_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGODB_URI)

# Database mapping berdasarkan kode_toko - dibaca dari .env
DB_MAPPING = {
    "KMT": os.getenv('DB_JUAL_KMT', 'db_hdpkmt'),
    "HGY": os.getenv('DB_JUAL_HGY', 'db_hdpayn_asli'),
    "HSA": os.getenv('DB_JUAL_HSA', 'db_hdpdmsa'),
    "KM2": os.getenv('DB_JUAL_KM2', 'db_hdpkmt2'),
    "MKT": os.getenv('DB_JUAL_MKT', 'db_hdpmkt'),
    "PGG": os.getenv('DB_JUAL_PGG', 'db_hdppgg'),
    "PMG": os.getenv('DB_JUAL_PMG', 'db_hdppmg'),
    "PMP": os.getenv('DB_JUAL_PMP', 'db_hdppml'),
    "HPM": os.getenv('DB_JUAL_HPM', 'db_hdppmr'),
    "HPS": os.getenv('DB_JUAL_HPS', 'db_hdppst'),
    "SAG": os.getenv('DB_JUAL_SAG', 'db_hdpsag')
}

TARGET_CATEGORY = "B278C07EC8B1C1B57F"
INPUT_FILE = "tt_member-1.json"

print("=" * 80)
print("Debug Lookup Script")
print("=" * 80)
print()

# Load sample data
print(f"Loading {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    members = json.load(f)

print(f"Total members: {len(members)}")
print()

# Cari member dengan kategori target dan information_transaction yang berisi data kosong
found_samples = 0
for member in members:
    if member.get("kategori") != TARGET_CATEGORY:
        continue
    
    info_trans = member.get("information_transaction", [])
    if not isinstance(info_trans, list):
        continue
    
    for trans_item in info_trans:
        if not isinstance(trans_item, dict):
            continue
        
        # Cek kondisi
        if (trans_item.get("nama_barang") == "-" and
            trans_item.get("no_faktur") == "-" and
            trans_item.get("kode_group") == "-" and
            trans_item.get("nama_atribut") == "-" and
            trans_item.get("kadar") == 0 and
            trans_item.get("kadar_modal") == 0 and
            trans_item.get("kode_barcode") == "-" and
            trans_item.get("kode_dept") == "-"):
            
            kode_toko = member.get("kode_toko", "")
            db_name = DB_MAPPING.get(kode_toko)
            
            print(f"Sample #{found_samples + 1}:")
            print(f"  Kode Toko: {kode_toko}")
            print(f"  Database: {db_name}")
            print(f"  Member ID: {member.get('_id', {}).get('$oid', 'N/A')}")
            print(f"  Transaction Item:")
            print(f"    no_faktur_jual: {trans_item.get('no_faktur_jual', 'TIDAK ADA')}")
            print(f"    deskripsi: {trans_item.get('deskripsi', 'TIDAK ADA')}")
            print(f"    berat: {trans_item.get('berat', 0)}")
            print(f"    harga: {trans_item.get('harga', 0)}")
            
            # Try lookup
            if db_name:
                no_faktur_jual = trans_item.get("no_faktur_jual")
                deskripsi = trans_item.get("deskripsi")
                
                print(f"\n  Mencoba lookup ke {db_name}.tt_jual_detail...")
                
                if no_faktur_jual and no_faktur_jual != "-":
                    print(f"    Searching by no_faktur_jual: {no_faktur_jual}")
                    try:
                        db = client[db_name]
                        result = db['tt_jual_detail'].find_one({"no_faktur_jual": no_faktur_jual})
                        if result:
                            print(f"    ✓ FOUND by no_faktur_jual!")
                            print(f"      nama_barang: {result.get('nama_barang', '-')}")
                            print(f"      no_faktur: {result.get('no_faktur', result.get('no_faktur_jual', '-'))}")
                            print(f"      kode_group: {result.get('kode_group', '-')}")
                            print(f"      kode_barcode: {result.get('kode_barcode', '-')}")
                        else:
                            print(f"    ✗ NOT FOUND by no_faktur_jual")
                    except Exception as e:
                        print(f"    ERROR: {str(e)}")
                
                if deskripsi and deskripsi != "-":
                    print(f"    Searching by deskripsi: {deskripsi}")
                    try:
                        db = client[db_name]
                        result = db['tt_jual_detail'].find_one({"deskripsi": deskripsi})
                        if result:
                            print(f"    ✓ FOUND by deskripsi!")
                            print(f"      nama_barang: {result.get('nama_barang', '-')}")
                            print(f"      no_faktur: {result.get('no_faktur', result.get('no_faktur_jual', '-'))}")
                            print(f"      kode_group: {result.get('kode_group', '-')}")
                            print(f"      kode_barcode: {result.get('kode_barcode', '-')}")
                        else:
                            print(f"    ✗ NOT FOUND by deskripsi")
                    except Exception as e:
                        print(f"    ERROR: {str(e)}")
                
                if (not no_faktur_jual or no_faktur_jual == "-") and (not deskripsi or deskripsi == "-"):
                    print(f"    ⚠ SKIP: Tidak ada no_faktur_jual atau deskripsi untuk lookup")
            else:
                print(f"  ⚠ Kode toko '{kode_toko}' tidak ada dalam mapping")
            
            print()
            
            found_samples += 1
            if found_samples >= 5:  # Tampilkan 5 sample saja
                break
    
    if found_samples >= 5:
        break

if found_samples == 0:
    print("Tidak ada sample yang match kondisi ditemukan")
else:
    print(f"Total sample ditampilkan: {found_samples}")

print()
print("=" * 80)
