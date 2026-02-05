import json
import os
import sys
from pymongo import ReadPreference, MongoClient
from collections import defaultdict
from config import Config
from dotenv import load_dotenv

load_dotenv()

def patch_no_faktur_complete(input_file=None, output_file=None):
    """
    Script untuk patch no_faktur dan nama_barang di information_transaction
    dengan lookup kode_barcode ke tt_jual_detail berdasarkan kode_toko
    
    Fitur:
    - Lookup berdasarkan kode_barcode ke database sesuai kode_toko
    - Update no_faktur dari no_faktur_jual di database
    - Update nama_barang dari database
    - Tambah field no_faktur_jual
    - Protect nilai yang sudah terisi (tidak di-overwrite jika bukan "-")
    """
    
    # Use default values if not provided
    if input_file is None:
        input_file = 'tmsambassg.tt_member_transformed.json'
    if output_file is None:
        output_file = 'tmsambassg.tt_member_no_faktur_COMPLETE.json'
    
    Config.print_config()
    
    # Database mapping berdasarkan kode_toko
    db_mapping = {
        'AN1': os.getenv('DB_JUAL_AN1', 'tmsambassg'),
        'AN2': os.getenv('DB_JUAL_AN2', 'tmsambaskj'),
        'AN3': os.getenv('DB_JUAL_AN3', 'tmsambasks'),
        'AN4': os.getenv('DB_JUAL_AN4', 'tmsambasmg'),
        'AN5': os.getenv('DB_JUAL_AN5', 'tmsambassj2'),
        'AN6': os.getenv('DB_JUAL_AN6', 'tmsambaskk'),
        'AN7': os.getenv('DB_JUAL_AN7', 'tmsambasbjg'),
    }
    
    print("\n" + "="*70)
    print("DATABASE MAPPING")
    print("="*70)
    for kode, db_name in sorted(db_mapping.items()):
        print(f"{kode}: {db_name}")
    print("="*70)
    
    print(f"\n[Step 1] Loading {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data):,} records")
    except FileNotFoundError:
        print(f"✗ File {input_file} not found!")
        return
    
    # Koneksi ke MongoDB
    print("\n[Step 2] Connecting to MongoDB...")
    try:
        client = Config.get_mongodb_client()
        db_connections = {}
        for kode, db_name in db_mapping.items():
            try:
                db_connections[kode] = client[db_name]
                # Test connection
                db_connections[kode]['tt_jual_detail'].count_documents({}, limit=1)
            except Exception as e:
                print(f"  ⚠ Warning: Could not connect to {kode} ({db_name}): {e}")
                db_connections[kode] = None
        
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return
    
    # Step 3: Build cache untuk semua kode_barcode per kode_toko
    print("\n[Step 3] Building cache from tt_jual_detail...")
    jual_cache = defaultdict(lambda: defaultdict(dict))  # {kode_toko: {kode_barcode: {...}}}
    batch_size = 1000
    
    # Collect semua unique kode_barcode per kode_toko
    print("  Collecting kode_barcode per kode_toko...")
    barcode_by_toko = defaultdict(set)
    
    for member in data:
        kode_toko = member.get('kode_toko', '')
        if 'information_transaction' in member and member['information_transaction']:
            for trans in member['information_transaction']:
                kode_barcode = trans.get('kode_barcode')
                if kode_barcode and kode_barcode != '-':
                    barcode_by_toko[kode_toko].add(kode_barcode)
    
    total_to_lookup = sum(len(barcodes) for barcodes in barcode_by_toko.values())
    print(f"  ✓ Found {total_to_lookup:,} unique kode_barcode across {len(barcode_by_toko)} kode_toko")
    
    # Lookup ke database untuk setiap kode_toko
    print("\n  Querying tt_jual_detail...")
    for kode_toko, barcode_set in sorted(barcode_by_toko.items()):
        db_name = db_mapping.get(kode_toko)
        
        if not db_name or kode_toko not in db_connections or db_connections[kode_toko] is None:
            print(f"  ⚠ Skipping {kode_toko}: No database connection")
            continue
        
        print(f"  Processing {kode_toko} ({db_name})...")
        
        db = db_connections[kode_toko]
        tt_jual_detail = db['tt_jual_detail'].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        
        barcode_list = list(barcode_set)
        toko_found = 0
        
        # Query dalam batch
        for i in range(0, len(barcode_list), batch_size):
            batch = barcode_list[i:i+batch_size]
            
            # Query untuk mendapatkan data lengkap (tidak perlu filter no_faktur)
            results = tt_jual_detail.find(
                {"kode_barcode": {"$in": batch}},
                {
                    "kode_barcode": 1,
                    "no_faktur_jual": 1,
                    "nama_barang": 1,
                    "berat": 1,
                    "_id": 0
                }
            )
            
            for doc in results:
                kode_barcode = doc.get('kode_barcode')
                if kode_barcode:
                    # Simpan data - ambil yang pertama jika ada duplikat
                    if kode_barcode not in jual_cache[kode_toko]:
                        jual_cache[kode_toko][kode_barcode] = {
                            'no_faktur_jual': doc.get('no_faktur_jual', '-'),
                            'nama_barang': doc.get('nama_barang', '-'),
                            'berat': doc.get('berat', 0)
                        }
                        toko_found += 1
        
        print(f"    ✓ Found {toko_found:,} kode_barcode dengan data")
    
    print(f"\n✓ Total cached: {sum(len(barcodes) for barcodes in jual_cache.values()):,} unique kode_barcode")
    
    # Close database
    client.close()
    
    # Step 4: Patch data menggunakan cache
    print("\n[Step 4] Patching data...")
    print("="*70)
    
    stats = {
        'no_faktur_patched': 0,
        'nama_barang_patched': 0,
        'no_faktur_jual_added': 0,
        'already_filled_no_faktur': 0,
        'already_filled_nama_barang': 0,
        'not_found': 0,
        'by_toko': defaultdict(int)
    }
    
    for idx, member in enumerate(data):
        kode_toko = member.get('kode_toko', '')
        
        if 'information_transaction' in member and member['information_transaction']:
            for trans in member['information_transaction']:
                kode_barcode = trans.get('kode_barcode')
                
                if not kode_barcode or kode_barcode == '-':
                    continue
                
                # Check cache
                if kode_toko in jual_cache and kode_barcode in jual_cache[kode_toko]:
                    jual_data = jual_cache[kode_toko][kode_barcode]
                    
                    # Update no_faktur jika "-" atau tidak ada
                    if not trans.get('no_faktur') or trans.get('no_faktur') == '-':
                        trans['no_faktur'] = jual_data['no_faktur_jual']
                        stats['no_faktur_patched'] += 1
                        stats['by_toko'][kode_toko] += 1
                    else:
                        stats['already_filled_no_faktur'] += 1
                    
                    # Update nama_barang jika "-" atau "8F"
                    if trans.get('nama_barang') in ['-', '8F']:
                        if jual_data['nama_barang'] and jual_data['nama_barang'] != '-':
                            trans['nama_barang'] = jual_data['nama_barang']
                            stats['nama_barang_patched'] += 1
                    else:
                        stats['already_filled_nama_barang'] += 1
                    
                    # Tambah field no_faktur_jual
                    trans['no_faktur_jual'] = jual_data['no_faktur_jual']
                    stats['no_faktur_jual_added'] += 1
                else:
                    stats['not_found'] += 1
        
        # Progress indicator
        if (idx + 1) % 5000 == 0:
            print(f"  Processed: {idx + 1:,}/{len(data):,} records")
    
    # Step 5: Save patched data
    print(f"\n[Step 5] Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ File saved successfully")
    
    # Print summary
    print("\n" + "="*70)
    print("PATCH NO_FAKTUR COMPLETE - SUMMARY")
    print("="*70)
    print(f"\nNo_Faktur Updates:")
    print(f"  ✓ Patched (dari '-'): {stats['no_faktur_patched']:,}")
    print(f"  → Already filled: {stats['already_filled_no_faktur']:,}")
    print(f"\nNama_Barang Updates:")
    print(f"  ✓ Patched (dari '-' atau '8F'): {stats['nama_barang_patched']:,}")
    print(f"  → Already filled: {stats['already_filled_nama_barang']:,}")
    print(f"\nNo_Faktur_Jual Field:")
    print(f"  ✓ Added: {stats['no_faktur_jual_added']:,}")
    print(f"\nDistribution by kode_toko:")
    for kode_toko in sorted(stats['by_toko'].keys()):
        db_name = db_mapping.get(kode_toko, 'UNKNOWN')
        print(f"  {kode_toko} ({db_name}): {stats['by_toko'][kode_toko]:,}")
    print(f"\nNot found: {stats['not_found']:,}")
    print("="*70)
    print(f"\n✓ Output saved to: {output_file}")

if __name__ == "__main__":
    try:
        # Get input and output files from command line arguments if provided
        input_arg = sys.argv[1] if len(sys.argv) > 1 else None
        output_arg = sys.argv[2] if len(sys.argv) > 2 else None
        patch_no_faktur_complete(input_arg, output_arg)
        print("\n✓ Data patching complete!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
        import traceback
        traceback.print_exc()
