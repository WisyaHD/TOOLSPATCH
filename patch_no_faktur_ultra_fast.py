from pymongo import ReadPreference
import json
import os
from collections import defaultdict
from config import Config

def patch_no_faktur_ultra_fast():
    """
    Versi ultra-fast untuk patch no_faktur di information_transaction 
    dengan lookup ke tt_jual_detail menggunakan kode_barcode
    
    Optimasi:
    - Batch lookup menggunakan $in operator
    - Cache semua data dalam memory
    - Single pass patching
    - Lookup ke database yang sesuai berdasarkan kode_toko
    """
    # Load konfigurasi
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
    
    print("\n" + "="*60)
    print("DATABASE MAPPING")
    print("="*60)
    for kode, db_name in sorted(db_mapping.items()):
        print(f"{kode}: {db_name}")
    print("="*60)
    
    # Input/output files  
    # Cari file dengan information_transaction
    possible_files = [
        'tmsambassg.tt_member_transformed.json',
        'backuptt_member/db_hdpayn_asli.tt_member.json',
        'sample_for_test.json',
        'backuptt_member/tt_member1.json',
        'IDHJY/db_hdpayn_asli.tt_member.json'
    ]
    
    input_file = None
    for f in possible_files:
        if os.path.exists(f):
            input_file = f
            break
    
    if not input_file:
        print("✗ No input file found with information_transaction!")
        return
        
    output_file = 'tmsambassg.tt_member_FINAL_COMPLETE.json'
    
    print(f"\nLoading {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data):,} records from {input_file}")
    except FileNotFoundError:
        print(f"✗ File {input_file} not found!")
        return
    
    # Koneksi ke MongoDB
    print("\nConnecting to MongoDB...")
    try:
        client = Config.get_mongodb_client()
        
        # Get all database connections
        db_connections = {}
        for kode, db_name in db_mapping.items():
            db_connections[kode] = client[db_name]
        
        print("✓ Connected to MongoDB successfully")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return
    
    # Step 1: Collect all unique kode_barcode yang perlu di-lookup, grouped by kode_toko
    print("\n[Step 1] Collecting kode_barcode to lookup...")
    barcode_by_toko = defaultdict(set)  # {kode_toko: set(kode_barcode)}
    total_items = 0
    items_need_lookup = 0
    
    for member in data:
        kode_toko = member.get('kode_toko', '')
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                total_items += 1
                if trans.get('no_faktur') == '-':
                    kode_barcode = trans.get('kode_barcode')
                    if kode_barcode and kode_barcode != '-':
                        barcode_by_toko[kode_toko].add(kode_barcode)
                        items_need_lookup += 1
    
    print(f"✓ Total transaction items: {total_items:,}")
    print(f"✓ Items need lookup: {items_need_lookup:,}")
    print(f"✓ Distribution by kode_toko:")
    for kode_toko in sorted(barcode_by_toko.keys()):
        db_name = db_mapping.get(kode_toko, 'UNKNOWN')
        print(f"  - {kode_toko}: {len(barcode_by_toko[kode_toko]):,} unique barcodes → {db_name}")
    
    # Step 2: Build cache dari tt_jual_detail untuk setiap database
    print("\n[Step 2] Building cache from tt_jual_detail per database...")
    jual_cache = defaultdict(lambda: defaultdict(list))  # {kode_toko: {kode_barcode: [data]}}
    batch_size = 1000
    total_fetched = 0
    
    for kode_toko, barcode_set in barcode_by_toko.items():
        db_name = db_mapping.get(kode_toko)
        if not db_name or kode_toko not in db_connections:
            print(f"  ⚠ Skipping {kode_toko}: No database mapping")
            continue
        
        print(f"\n  Processing {kode_toko} → {db_name}")
        
        db = db_connections[kode_toko]
        tt_jual_detail = db['tt_jual_detail'].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        
        barcode_list = list(barcode_set)
        toko_fetched = 0
        
        for i in range(0, len(barcode_list), batch_size):
            batch = barcode_list[i:i+batch_size]
            
            # Query dengan projection untuk mengambil field yang diperlukan saja
            results = tt_jual_detail.find(
                {
                    "kode_barcode": {"$in": batch}, 
                    "no_faktur_jual": {"$ne": "-", "$exists": True}
                },
                {
                    "kode_barcode": 1, 
                    "no_faktur_jual": 1, 
                    "nama_barang": 1, 
                    "berat": 1,
                    "_id": 0
                }
            )
            
            batch_count = 0
            for doc in results:
                kode_barcode = doc.get('kode_barcode')
                jual_cache[kode_toko][kode_barcode].append({
                    'no_faktur_jual': doc.get('no_faktur_jual', '-'),
                    'nama_barang': doc.get('nama_barang', '-'),
                    'berat': doc.get('berat', 0)
                })
                batch_count += 1
                toko_fetched += 1
                total_fetched += 1
            
            # Progress indicator
            if (i + batch_size) % 5000 == 0 or i + batch_size >= len(barcode_list):
                print(f"    Progress: {min(i + batch_size, len(barcode_list)):,}/{len(barcode_list):,} barcodes checked, {toko_fetched:,} records found")
        
        print(f"    ✓ Cached {len(jual_cache[kode_toko]):,} unique barcodes with {toko_fetched:,} records")
    
    print(f"\n✓ Total cached: {total_fetched:,} records from all databases")
    
    # Close database connection
    client.close()
    print("✓ Database connection closed")
    
    # Step 3: Patch data menggunakan cache
    print("\n[Step 3] Patching data using cache...")
    print("="*60)
    
    stats = {
        'patched_count': 0,
        'not_found_count': 0,
        'already_filled_count': 0,
        'no_barcode_count': 0,
        'nama_barang_updated': 0,
        'berat_updated': 0,
        'by_toko': defaultdict(int)
    }
    
    for idx, member in enumerate(data):
        kode_toko = member.get('kode_toko', '')
        
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                # Hanya proses jika no_faktur adalah "-"
                if trans.get('no_faktur') == '-':
                    kode_barcode = trans.get('kode_barcode')
                    
                    if not kode_barcode or kode_barcode == '-':
                        stats['no_barcode_count'] += 1
                        continue
                    
                    # Check cache untuk kode_toko dan kode_barcode
                    if kode_toko in jual_cache and kode_barcode in jual_cache[kode_toko]:
                        # Ambil data pertama dari list (jika ada multiple)
                        jual_data = jual_cache[kode_toko][kode_barcode][0]
                        
                        # Update no_faktur dengan no_faktur_jual dari tt_jual_detail
                        trans['no_faktur'] = jual_data['no_faktur_jual']
                        
                        stats['patched_count'] += 1
                        stats['by_toko'][kode_toko] += 1
                        
                        # Bonus: update nama_barang jika masih "-" atau "8F"
                        if trans.get('nama_barang') in ['-', '8F'] and jual_data['nama_barang'] != '-':
                            trans['nama_barang'] = jual_data['nama_barang']
                            stats['nama_barang_updated'] += 1
                        
                        # Bonus: update berat jika 0 atau tidak ada
                        if not trans.get('berat') or trans.get('berat') == 0:
                            if jual_data['berat']:
                                trans['berat'] = jual_data['berat']
                                stats['berat_updated'] += 1
                    else:
                        stats['not_found_count'] += 1
                else:
                    stats['already_filled_count'] += 1
        
        # Progress indicator
        if (idx + 1) % 1000 == 0:
            print(f"  Processed: {idx + 1:,}/{len(data):,} records")
    
    # Step 4: Save patched data
    print(f"\n[Step 4] Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ File saved successfully")
    
    # Print summary
    print("\n" + "="*60)
    print("PATCH NO_FAKTUR - SUMMARY")
    print("="*60)
    print(f"Total records processed: {len(data):,}")
    print(f"Total transaction items: {total_items:,}")
    print()
    print(f"✓ No_faktur patched: {stats['patched_count']:,}")
    print(f"  - Nama_barang also updated: {stats['nama_barang_updated']:,}")
    print(f"  - Berat also updated: {stats['berat_updated']:,}")
    print()
    print(f"  Distribution by kode_toko:")
    for kode_toko in sorted(stats['by_toko'].keys()):
        db_name = db_mapping.get(kode_toko, 'UNKNOWN')
        print(f"    {kode_toko} ({db_name}): {stats['by_toko'][kode_toko]:,}")
    print()
    print(f"  Already have no_faktur: {stats['already_filled_count']:,}")
    print(f"  Without kode_barcode: {stats['no_barcode_count']:,}")
    print(f"  Not found in tt_jual_detail: {stats['not_found_count']:,}")
    print("="*60)
    
    # Calculate coverage
    if items_need_lookup > 0:
        coverage = (stats['patched_count'] / items_need_lookup) * 100
        print(f"\nCoverage: {coverage:.2f}% ({stats['patched_count']:,}/{items_need_lookup:,})")
    
    print(f"\n✓ Output saved to: {output_file}")

if __name__ == "__main__":
    try:
        patch_no_faktur_ultra_fast()
        print("\n✓ Data patching complete!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
