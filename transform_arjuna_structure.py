import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB Connection - get from .env or use default
MONGODB_URI = os.getenv('MONGODB_URI', "mongodb://nsi:CPJQhiZ8x8k5@103.93.130.182:27017,103.235.75.134:27017,157.66.35.67:27017,202.10.47.79:27017/tmsambassg?authSource=admin&replicaSet=rs0&readPreference=secondaryPreferred&serverSelectionTimeoutMS=5000&connectTimeoutMS=5000&socketTimeoutMS=5000&retryWrites=true&w=majority")
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000, socketTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"⚠️  MongoDB connection failed: {str(e)}")
    print("   Transform will continue without DB lookup")
    ENABLE_DB_LOOKUP = False
    client = None

# Database mapping - load from environment variables
SAMBAS_DATABASES = {}

# Load DB_JUAL_* from environment
for key, value in os.environ.items():
    if key.startswith('DB_JUAL_') and key != 'DB_JUAL':
        # Extract branch code (e.g., DB_JUAL_AN1 -> AN1)
        branch_code = key.replace('DB_JUAL_', '')
        SAMBAS_DATABASES[branch_code] = value

# Fallback to hardcoded mapping if no environment variables found
if not SAMBAS_DATABASES:
    SAMBAS_DATABASES = {
        "AN4": "tmsambasmg",
        "AN3": "tmsambasks",
        "AN2": "tmsambaskj",
        "AN6": "tmsambaskk",
        "AN7": "tmsambasbjg",
        "AN5": "tmsambassj2",
        "AN1": "tmsambassg"
    }

# File settings - can be overridden by command line args
import sys
if len(sys.argv) >= 3:
    INPUT_FILE = sys.argv[1]
    OUTPUT_FILE = sys.argv[2]
else:
    INPUT_FILE = "tmsambassg.tt_member.json"
    OUTPUT_FILE = "tmsambassg.tt_member_transformed.json"
TARGET_CATEGORY = "B278C07EC8B1C1B57F"

# Performance setting - set to True to enable database lookups for no_faktur
ENABLE_DB_LOOKUP = True

def get_database_by_kode_toko(kode_toko):
    """Mendapatkan nama database berdasarkan kode_toko"""
    return SAMBAS_DATABASES.get(kode_toko, None)

def lookup_tt_jual_detail(db_name, no_faktur_jual=None, kode_barcode=None):
    """Lookup data dari tt_jual_detail dengan prioritas no_faktur_jual"""
    if not db_name or not client:
        return None
    
    try:
        db = client[db_name]
        collection = db['tt_jual_detail']
        
        # Priority 1: Try lookup by no_faktur_jual (most accurate)
        if no_faktur_jual and no_faktur_jual != "-":
            result = collection.find_one({"no_faktur_jual": no_faktur_jual}, maxTimeMS=3000)
            if result:
                return result
        
        # Priority 2: Try lookup by kode_barcode
        if kode_barcode and kode_barcode != "-":
            result = collection.find_one({"kode_barcode": kode_barcode}, maxTimeMS=3000)
            if result:
                return result
    except Exception as e:
        # Silently ignore lookup errors to continue processing
        pass
    
    return None

def transform_member_structure(old_member):
    """
    Transform dari struktur lama ke struktur baru dengan information_transaction
    """
    # Cek apakah data sudah dalam format baru (punya information_transaction)
    if "information_transaction" in old_member and old_member.get("information_transaction"):
        # Data sudah dalam format baru, pastikan semua field transaction lengkap
        info_trans = old_member.get("information_transaction", [])
        if isinstance(info_trans, list):
            for trans in info_trans:
                if not isinstance(trans, dict):
                    continue
                trans.setdefault("nama_barang", old_member.get("nama_barang", "-"))
                trans.setdefault("nama_atribut", "-")
                trans.setdefault("no_faktur", old_member.get("no_faktur_jual", "-"))
                trans.setdefault("berat", old_member.get("berat", 0))
                trans.setdefault("kadar", 0)
                trans.setdefault("kadar_cetak", "-")
                trans.setdefault("kadar_modal", 0)
                trans.setdefault("kode_barcode", old_member.get("deskripsi", "-"))
                trans.setdefault("kode_dept", "-")
                trans.setdefault("kode_group", "-")
                trans.setdefault("harga", int(old_member.get("jumlah_rp", 0)) if old_member.get("jumlah_rp") else 0)
                trans.setdefault("no_faktur_jual", old_member.get("no_faktur_jual", "-"))
                trans.setdefault("lookup_source", "-")
                trans.setdefault("lookup_db", "-")
        return old_member
    
    # Extract data dari struktur lama
    no_faktur_jual = old_member.get("no_faktur_jual", "-")
    nama_barang = old_member.get("nama_barang", "-")
    berat = old_member.get("berat", "-")
    kode_toko = old_member.get("kode_toko", "")
    deskripsi = old_member.get("deskripsi", "-")
    
    # Coba lookup ke tt_jual_detail untuk mendapatkan data lengkap (only if enabled)
    tt_jual_data = None
    db_name = None
    
    if ENABLE_DB_LOOKUP:
        db_name = get_database_by_kode_toko(kode_toko)
        
        if db_name:
            # Prioritas 1: Lookup dengan no_faktur_jual
            if no_faktur_jual and no_faktur_jual != "-":
                tt_jual_data = lookup_tt_jual_detail(db_name, no_faktur_jual=no_faktur_jual)
            
            # Prioritas 2: Jika tidak ditemukan, coba dengan deskripsi sebagai kode_barcode
            if not tt_jual_data and deskripsi and deskripsi != "-":
                tt_jual_data = lookup_tt_jual_detail(db_name, kode_barcode=deskripsi)
        else:
            print(f"⚠️  Warning: Database tidak ditemukan untuk kode_toko: {kode_toko}")
    
    # Buat struktur baru
    new_member = {
        "_id": old_member.get("_id"),
        "no_trx": old_member.get("no_trx"),
        "tgl_trx": old_member.get("tgl_trx"),
        "kode_member": old_member.get("kode_member"),
        "nama_customer": "-",
        "alamat_customer": "-",
        "no_hp": "-",
        "kode_toko": kode_toko,
        "kategori": old_member.get("kategori"),
        "deskripsi": f"PENJUALAN {no_faktur_jual}, HARGA TOTAL Rp {old_member.get('jumlah_rp', '0')}" if no_faktur_jual != "-" else deskripsi,
        "keterangan": "-",
        "berat": "-",
        "jumlah_rp": old_member.get("jumlah_rp", "0"),
        "poin_awal": old_member.get("poin_awal", 0),
        "poin": old_member.get("poin", 0),
        "poin_bak": 0,
        "poin_akhir": old_member.get("poin_akhir", 0),
        "no_faktur_jual": "-",
        "nama_barang": "-",
        "input_by": old_member.get("input_by", "-"),
        "status": old_member.get("status", "OPEN"),
        "information_transaction": [],
        "schema_version": 2,
        "__v": old_member.get("__v", 0)
    }
    
    # Buat transaction item dari data lama atau tt_jual_detail
    transaction_item = {}
    
    if tt_jual_data:
        # Ambil data dari tt_jual_detail
        barang = tt_jual_data.get("barang", {})
        no_faktur_from_db = tt_jual_data.get("no_faktur_jual", "-")
        
        transaction_item = {
            "nama_barang": barang.get("nama_barang", tt_jual_data.get("nama_barang", nama_barang if nama_barang != "-" else "8F")),
            "nama_atribut": barang.get("nama_atribut", tt_jual_data.get("nama_atribut", "8F")),
            "no_faktur": no_faktur_from_db,
            "berat": float(berat) if berat != "-" and berat else tt_jual_data.get("berat", 0),
            "kadar": barang.get("kadar", tt_jual_data.get("kadar", 0)),
            "kadar_cetak": barang.get("kadar_cetak", tt_jual_data.get("kadar_cetak", "-")),
            "kadar_modal": barang.get("kadar_modal", tt_jual_data.get("kadar_modal", 0)),
            "kode_barcode": tt_jual_data.get("kode_barcode", deskripsi if deskripsi != "-" else "-"),
            "kode_dept": tt_jual_data.get("kode_dept", "-"),
            "kode_group": tt_jual_data.get("kode_group", "-"),
            "harga": int(old_member.get("jumlah_rp", 0)),
            "no_faktur_jual": no_faktur_from_db,
            "lookup_source": "tt_jual_detail",
            "lookup_db": db_name if db_name else "-"
        }
    else:
        # Gunakan data dari struktur lama
        transaction_item = {
            "nama_barang": nama_barang if nama_barang != "-" else "8F",
            "nama_atribut": "8F",
            "no_faktur": no_faktur_jual if no_faktur_jual != "-" else "-",
            "berat": float(berat) if berat != "-" and berat else 0,
            "kadar": 0,
            "kadar_cetak": "-",
            "kadar_modal": 0,
            "kode_barcode": deskripsi if deskripsi != "-" else "-",
            "kode_dept": "-",
            "kode_group": "-",
            "harga": int(old_member.get("jumlah_rp", 0))
        }
    
    # Tambahkan transaction item ke array
    if transaction_item:
        new_member["information_transaction"].append(transaction_item)
    
    return new_member

def transform_file():
    """Transform file JSON dari struktur lama ke baru"""
    start_time = datetime.now()
    
    print("=" * 80)
    print("🔄 TRANSFORM ARJUNA STRUCTURE")
    print("=" * 80)
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Target kategori: {TARGET_CATEGORY}")
    print(f"Database lookup: {'ENABLED ✅' if ENABLE_DB_LOOKUP else 'DISABLED (Fast Mode)'}")
    print(f"Database mapping: {len(SAMBAS_DATABASES)} cabang loaded")
    if SAMBAS_DATABASES:
        for kode, db in list(SAMBAS_DATABASES.items())[:3]:
            print(f"  - {kode}: {db}")
        if len(SAMBAS_DATABASES) > 3:
            print(f"  ... dan {len(SAMBAS_DATABASES) - 3} lainnya")
    print()
    
    # Load data
    print(f"Loading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            members = json.load(f)
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return
    
    total_members = len(members)
    print(f"Total members: {total_members}\n")
    
    # Transform each member
    print("Transforming members...")
    transformed_members = []
    found_in_db = 0
    
    for idx, member in enumerate(members, 1):
        # Filter by category
        if member.get("kategori") != TARGET_CATEGORY:
            continue
        
        new_member = transform_member_structure(member)
        
        # Check if data was enriched from database
        if new_member["information_transaction"]:
            trans = new_member["information_transaction"][0]
            # Count as found if no_faktur is filled (not "-")
            if trans.get("no_faktur") and trans.get("no_faktur") != "-":
                found_in_db += 1
        
        transformed_members.append(new_member)
        
        if idx % 10000 == 0:
            print(f"  Processed {idx}/{total_members} members...")
    
    print(f"\n✅ Transformation complete!")
    print(f"Total transformed: {len(transformed_members)}")
    print(f"Enriched from tt_jual_detail: {found_in_db}")
    
    # Save
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(transformed_members, f, ensure_ascii=False, indent=2)
        print(f"✅ Successfully saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return
    
    # Stats
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 80)
    print(f"⏱️  Total time: {duration:.2f} seconds")
    print("=" * 80)

if __name__ == "__main__":
    transform_file()
