import json
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from collections import defaultdict

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
    "SAG": os.getenv('DB_JUAL_SAG', 'db_hdpsag'),
    "HSL": os.getenv('DB_JUAL_HSL', 'db_hdphsl'),
    "SAO": os.getenv('DB_JUAL_SAO', 'db_hdpsao'),
    "HD": os.getenv('DB_JUAL_HD', 'db_hdpayn_asli'),
    "SA": os.getenv('DB_JUAL_SA', 'db_hdpsa'),
    "PML": os.getenv('DB_JUAL_PML', 'db_hdppml'),
    "SL": os.getenv('DB_JUAL_SL', 'db_hdpsl'),
    "PGN": os.getenv('DB_JUAL_PGN', 'db_hdppgn'),
    # Mapping untuk database Arjuna
    "ARJ": os.getenv('DB_JUAL_ARJ', 'db_arjnjtb'),
    "RJN": os.getenv('DB_JUAL_RJN', 'db_arjnptr'),
    "RJ2": os.getenv('DB_JUAL_RJ2', 'db_arjnptr2'),
    "APT": os.getenv('DB_JUAL_APT', 'db_arjnputri'),
    "EAJ": os.getenv('DB_JUAL_ARJ', 'db_arjnjtb'),  # EAJ maps to ARJ database
    "JNK": os.getenv('DB_JUAL_ARJ', 'db_arjnjtb')   # JNK maps to ARJ database
}

# Target kategori
TARGET_CATEGORY = "B278C07EC8B1C1B57F"

# File input JSON - can be overridden by command line args
import sys
if len(sys.argv) >= 3:
    INPUT_FILE = sys.argv[1]
    OUTPUT_FILE = sys.argv[2]
else:
    INPUT_FILE = "tt_member123.json"
    OUTPUT_FILE = "tt_member123_patched.json"

def get_database_by_kode_toko(kode_toko):
    """Mendapatkan nama database berdasarkan kode_toko"""
    return DB_MAPPING.get(kode_toko, None)

def extract_data_from_tt_jual(tt_jual_data):
    """
    Extract data yang diperlukan dari tt_jual_detail
    """
    if not tt_jual_data:
        return {
            "nama_barang": "-",
            "no_faktur": "-",
            "kode_group": "-",
            "nama_atribut": "-",
            "kadar": 0,
            "kadar_modal": 0,
            "kode_barcode": "-",
            "kode_dept": "-",
            "kadar_cetak": "-"
        }
    
    extracted = {}
    barang = tt_jual_data.get("barang", {})
    
    extracted["nama_barang"] = barang.get("nama_barang", tt_jual_data.get("nama_barang", "-"))
    extracted["nama_atribut"] = barang.get("nama_atribut", tt_jual_data.get("nama_atribut", "-"))
    extracted["kadar"] = barang.get("kadar", tt_jual_data.get("kadar", 0))
    extracted["kadar_modal"] = barang.get("kadar_modal", tt_jual_data.get("kadar_modal", 0))
    extracted["kadar_cetak"] = barang.get("kadar_cetak", tt_jual_data.get("kadar_cetak", "-"))
    extracted["no_faktur"] = tt_jual_data.get("no_faktur_jual", "-")
    extracted["kode_group"] = tt_jual_data.get("kode_group", "-")
    extracted["kode_dept"] = tt_jual_data.get("kode_dept", "-")
    extracted["kode_barcode"] = tt_jual_data.get("kode_barcode", tt_jual_data.get("kode_barang", "-"))
    
    for field in ["nama_barang", "no_faktur", "kode_group", "nama_atribut", "kode_barcode", "kode_dept", "kadar_cetak"]:
        if field not in extracted or extracted[field] is None:
            extracted[field] = "-"
    
    for field in ["kadar", "kadar_modal"]:
        if field not in extracted or extracted[field] is None:
            extracted[field] = 0
    
    return extracted

def batch_lookup_all_databases(members_by_db):
    """
    OPTIMIZED: Batch lookup untuk semua database sekaligus
    Mengambil semua data yang diperlukan dalam 1 query per database
    """
    print("🚀 OPTIMIZED BATCH LOOKUP - Loading data from databases...")
    cache = {}
    
    for db_name, lookup_data in members_by_db.items():
        if not lookup_data['fakturs'] and not lookup_data['barcodes'] and not lookup_data['berats']:
            continue
            
        print(f"  Loading from {db_name}...")
        db = client[db_name]
        collection = db['tt_jual_detail']
        
        # Build query with $or to get no_faktur_jual, kode_barcode, and berat
        query_conditions = []
        
        if lookup_data['fakturs']:
            query_conditions.append({"no_faktur_jual": {"$in": list(lookup_data['fakturs'])}})
        
        if lookup_data['barcodes']:
            query_conditions.append({"kode_barcode": {"$in": list(lookup_data['barcodes'])}})
        
        if lookup_data['berats']:
            query_conditions.append({"berat": {"$in": list(lookup_data['berats'])}})
        
        if query_conditions:
            query = {"$or": query_conditions} if len(query_conditions) > 1 else query_conditions[0]
            
            # Fetch all in one query!
            results = list(collection.find(query))
            print(f"    Found {len(results)} records")
            
            # Cache by no_faktur_jual
            for doc in results:
                if doc.get("no_faktur_jual"):
                    cache_key = f"{db_name}|faktur|{doc['no_faktur_jual']}"
                    cache[cache_key] = doc
                
                # Cache by kode_barcode
                if doc.get("kode_barcode"):
                    cache_key = f"{db_name}|barcode|{doc['kode_barcode']}"
                    cache[cache_key] = doc
                
                # Cache by berat
                if doc.get("berat"):
                    cache_key = f"{db_name}|berat|{doc['berat']}"
                    cache[cache_key] = doc
    
    print(f"✅ Cache loaded with {len(cache)} entries\n")
    return cache

def patch_member_data():
    """
    ULTRA FAST: Patch data dengan batch lookup strategy
    """
    print(f"Loading {INPUT_FILE}...")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            members = json.load(f)
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return
    
    total_members = len(members)
    print(f"Total members: {total_members}")
    print(f"Target kategori: {TARGET_CATEGORY}\n")
    
    # PHASE 1: Collect all lookup keys by database
    print("📊 PHASE 1: Analyzing members and collecting lookup keys...")
    members_by_db = defaultdict(lambda: {'fakturs': set(), 'barcodes': set(), 'berats': set()})
    target_members = []
    
    for member in members:
        if member.get("kategori") != TARGET_CATEGORY:
            continue
        
        kode_toko = member.get("kode_toko", "")
        db_name = get_database_by_kode_toko(kode_toko)
        
        if not db_name:
            continue
        
        info_trans = member.get("information_transaction", [])
        if not isinstance(info_trans, list):
            continue
        
        # Check if has items to patch
        has_target = False
        for trans_item in info_trans:
            if (trans_item.get("nama_barang") in ["-", "8F"] and
                trans_item.get("no_faktur") == "-" and
                trans_item.get("kode_barcode") == "-"):
                has_target = True
                break
        
        if has_target:
            target_members.append(member)
            no_faktur_jual = member.get("no_faktur_jual")
            deskripsi = member.get("deskripsi")
            
            if no_faktur_jual and no_faktur_jual != "-":
                members_by_db[db_name]['fakturs'].add(no_faktur_jual)
            
            if deskripsi and deskripsi != "-":
                # Jika deskripsi berformat faktur (ada dash), lookup sebagai no_faktur_jual
                # Jika numerik, lookup sebagai kode_barcode
                if '-' in deskripsi:
                    members_by_db[db_name]['fakturs'].add(deskripsi)
                else:
                    members_by_db[db_name]['barcodes'].add(deskripsi)
            
            # Collect berat from information_transaction
            for trans_item in info_trans:
                if not isinstance(trans_item, dict):
                    continue
                berat = trans_item.get("berat")
                if berat and berat > 0:
                    members_by_db[db_name]['berats'].add(berat)
    
    print(f"Found {len(target_members)} members to patch")
    print(f"Will query {len(members_by_db)} databases\n")
    
    # PHASE 2: Batch lookup all data
    cache = batch_lookup_all_databases(members_by_db)
    
    # PHASE 3: Apply patches using cache
    print("⚡ PHASE 3: Applying patches using cache...")
    updated = 0
    found_count = 0
    not_found_count = 0
    found_by_faktur = 0
    found_by_barcode = 0
    found_by_berat = 0
    member_faktur_updated = 0
    
    for idx, member in enumerate(target_members, 1):
        kode_toko = member.get("kode_toko", "")
        db_name = get_database_by_kode_toko(kode_toko)
        no_faktur_jual = member.get("no_faktur_jual")
        deskripsi = member.get("deskripsi")
        
        # Update member.no_faktur_jual from tt_jual_detail lookup
        if db_name:
            lookup_result = None
            
            # Try lookup by no_faktur_jual
            if no_faktur_jual and no_faktur_jual != "-":
                cache_key = f"{db_name}|faktur|{no_faktur_jual}"
                lookup_result = cache.get(cache_key)
            
            # Try lookup by deskripsi (as no_faktur_jual or kode_barcode)
            if not lookup_result and deskripsi and deskripsi != "-":
                if '-' in deskripsi:
                    cache_key = f"{db_name}|faktur|{deskripsi}"
                else:
                    cache_key = f"{db_name}|barcode|{deskripsi}"
                lookup_result = cache.get(cache_key)
            
            # Update member.no_faktur_jual if found in tt_jual_detail
            if lookup_result and lookup_result.get("no_faktur_jual"):
                tt_jual_no_faktur = lookup_result.get("no_faktur_jual")
                if member.get("no_faktur_jual") != tt_jual_no_faktur:
                    member["no_faktur_jual"] = tt_jual_no_faktur
                    member_faktur_updated += 1
        
        info_trans = member.get("information_transaction", [])
        
        for trans_item in info_trans:
            if not isinstance(trans_item, dict):
                continue
            
            if (trans_item.get("nama_barang") in ["-", "8F"] and
                trans_item.get("no_faktur") == "-" and
                trans_item.get("kode_group") == "-" and
                trans_item.get("nama_atribut") == "-" and
                trans_item.get("kadar") == 0 and
                trans_item.get("kadar_modal") == 0 and
                trans_item.get("kode_barcode") == "-" and
                trans_item.get("kode_dept") == "-"):
                
                # Lookup from cache
                tt_jual_data = None
                lookup_method = None
                
                # Try no_faktur_jual first
                if no_faktur_jual and no_faktur_jual != "-":
                    cache_key = f"{db_name}|faktur|{no_faktur_jual}"
                    tt_jual_data = cache.get(cache_key)
                    if tt_jual_data:
                        lookup_method = "no_faktur_jual"
                
                # Try deskripsi as no_faktur_jual if not found
                if not tt_jual_data and deskripsi and deskripsi != "-" and '-' in deskripsi:
                    cache_key = f"{db_name}|faktur|{deskripsi}"
                    tt_jual_data = cache.get(cache_key)
                    if tt_jual_data:
                        lookup_method = "no_faktur_jual (from deskripsi)"
                
                # Try kode_barcode if not found (for numeric deskripsi)
                if not tt_jual_data and deskripsi and deskripsi != "-" and '-' not in deskripsi:
                    cache_key = f"{db_name}|barcode|{deskripsi}"
                    tt_jual_data = cache.get(cache_key)
                    if tt_jual_data:
                        lookup_method = "kode_barcode"
                
                # Try berat if still not found
                if not tt_jual_data:
                    berat = trans_item.get("berat")
                    if berat and berat > 0:
                        cache_key = f"{db_name}|berat|{berat}"
                        tt_jual_data = cache.get(cache_key)
                        if tt_jual_data:
                            lookup_method = "berat"
                
                if tt_jual_data:
                    found_count += 1
                    if lookup_method == "no_faktur_jual" or lookup_method == "no_faktur_jual (from deskripsi)":
                        found_by_faktur += 1
                    elif lookup_method == "kode_barcode":
                        found_by_barcode += 1
                    elif lookup_method == "berat":
                        found_by_berat += 1
                else:
                    not_found_count += 1
                
                # Extract and update
                extracted_data = extract_data_from_tt_jual(tt_jual_data)
                
                trans_item["nama_barang"] = extracted_data["nama_barang"]
                trans_item["no_faktur"] = extracted_data["no_faktur"]
                trans_item["kode_group"] = extracted_data["kode_group"]
                trans_item["nama_atribut"] = extracted_data["nama_atribut"]
                trans_item["kadar"] = extracted_data["kadar"]
                trans_item["kadar_modal"] = extracted_data["kadar_modal"]
                trans_item["kode_barcode"] = extracted_data["kode_barcode"]
                trans_item["kode_dept"] = extracted_data["kode_dept"]
                trans_item["kadar_cetak"] = extracted_data["kadar_cetak"]
                
                updated += 1
        
        if idx % 1000 == 0:
            print(f"  Processed {idx}/{len(target_members)} members...")
    
    print(f"\n✅ PHASE 3 COMPLETE!\n")
    print("=" * 80)
    print(f"Total members processed: {total_members}")
    print(f"Total target members: {len(target_members)}")
    print(f"Member no_faktur_jual updated: {member_faktur_updated}")
    print(f"Total transactions updated: {updated}")
    print(f"Data found: {found_count}")
    print(f"  - via no_faktur_jual: {found_by_faktur}")
    print(f"  - via kode_barcode: {found_by_barcode}")
    print(f"  - via berat: {found_by_berat}")
    print(f"Data not found: {not_found_count}")
    print("=" * 80)
    
    # Save
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(members, f, ensure_ascii=False, indent=2)
        print(f"✅ Successfully saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Error saving file: {str(e)}")

if __name__ == "__main__":
    print("=" * 80)
    print("⚡ ULTRA FAST PATCH - Batch Lookup Strategy")
    print("=" * 80)
    print()
    
    import time
    start_time = time.time()
    
    patch_member_data()
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print()
    print("=" * 80)
    print(f"⏱️  Total time: {elapsed:.2f} seconds")
    print("=" * 80)
