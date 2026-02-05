from pymongo import ReadPreference
import json
from collections import defaultdict
from config import Config

def patch_kmt_with_cache():
    """
    Script untuk patch file KMT.tt_member.json dengan lookup menggunakan cache
    untuk performa lebih cepat
    """
    # Load konfigurasi
    Config.print_config()
    
    # Load file JSON
    input_file = 'KMT.tt_member.json'
    output_file = 'KMT.tt_member_patched.json'
    
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
        
        # Get databases
        db_jual = client[Config.DB_JUAL]
        db_beli = client[Config.DB_BELI]
        
        # Get collections dengan read preference secondary
        tt_jual_detail = db_jual[Config.COLLECTION_TT_JUAL_DETAIL].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        tt_beli_detail = db_beli[Config.COLLECTION_TT_BELI_DETAIL].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        
        print("✓ Connected to MongoDB successfully")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return
    
    # Collect all unique no_faktur yang perlu di-lookup
    print("\nCollecting no_faktur to lookup...")
    faktur_set = set()
    
    for member in data:
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                if trans.get('kode_barcode') == '-':
                    no_faktur = trans.get('no_faktur')
                    if no_faktur:
                        faktur_set.add(no_faktur)
    
    print(f"✓ Found {len(faktur_set):,} unique no_faktur to lookup")
    
    # Build cache dari tt_jual_detail
    print("\nBuilding cache from tt_jual_detail...")
    jual_cache = {}
    faktur_list = list(faktur_set)
    batch_size = 1000
    
    for i in range(0, len(faktur_list), batch_size):
        batch = faktur_list[i:i+batch_size]
        results = tt_jual_detail.find(
            {"no_faktur": {"$in": batch}, "kode_barcode": {"$ne": "-"}},
            {"no_faktur": 1, "kode_barcode": 1, "nama_barang": 1, "berat": 1}
        )
        
        for doc in results:
            jual_cache[doc['no_faktur']] = {
                'kode_barcode': doc.get('kode_barcode', '-'),
                'nama_barang': doc.get('nama_barang', '-'),
                'berat': doc.get('berat', 0)
            }
        
        if (i + batch_size) % 10000 == 0:
            print(f"Loaded: {min(i + batch_size, len(faktur_list)):,} / {len(faktur_list):,}")
    
    print(f"✓ Cached {len(jual_cache):,} records from tt_jual_detail")
    
    # Build cache dari tt_beli_detail untuk faktur yang tidak ada di jual
    remaining_faktur = faktur_set - set(jual_cache.keys())
    print(f"\nBuilding cache from tt_beli_detail for remaining {len(remaining_faktur):,} faktur...")
    
    beli_cache = {}
    remaining_list = list(remaining_faktur)
    
    for i in range(0, len(remaining_list), batch_size):
        batch = remaining_list[i:i+batch_size]
        results = tt_beli_detail.find(
            {"no_faktur": {"$in": batch}, "kode_barcode": {"$ne": "-"}},
            {"no_faktur": 1, "kode_barcode": 1, "nama_barang": 1, "berat": 1}
        )
        
        for doc in results:
            beli_cache[doc['no_faktur']] = {
                'kode_barcode': doc.get('kode_barcode', '-'),
                'nama_barang': doc.get('nama_barang', '-'),
                'berat': doc.get('berat', 0)
            }
        
        if (i + batch_size) % 10000 == 0:
            print(f"Loaded: {min(i + batch_size, len(remaining_list)):,} / {len(remaining_list):,}")
    
    print(f"✓ Cached {len(beli_cache):,} records from tt_beli_detail")
    
    # Close database connection
    client.close()
    
    # Patch data menggunakan cache
    print("\nPatching data using cache...")
    print("="*60)
    
    patched_count = 0
    lookup_jual_count = 0
    lookup_beli_count = 0
    not_found_count = 0
    
    for idx, member in enumerate(data):
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                if trans.get('kode_barcode') == '-':
                    no_faktur = trans.get('no_faktur')
                    
                    if no_faktur:
                        # Check jual cache
                        if no_faktur in jual_cache:
                            jual_data = jual_cache[no_faktur]
                            trans['kode_barcode'] = jual_data['kode_barcode']
                            if jual_data['nama_barang'] != '-':
                                trans['nama_barang'] = jual_data['nama_barang']
                            if jual_data['berat'] and trans.get('berat') == 0:
                                trans['berat'] = jual_data['berat']
                            trans['lookup_source'] = 'tt_jual_detail'
                            lookup_jual_count += 1
                            patched_count += 1
                        # Check beli cache
                        elif no_faktur in beli_cache:
                            beli_data = beli_cache[no_faktur]
                            trans['kode_barcode'] = beli_data['kode_barcode']
                            if beli_data['nama_barang'] != '-':
                                trans['nama_barang'] = beli_data['nama_barang']
                            if beli_data['berat'] and trans.get('berat') == 0:
                                trans['berat'] = beli_data['berat']
                            trans['lookup_source'] = 'tt_beli_detail'
                            lookup_beli_count += 1
                            patched_count += 1
                        else:
                            not_found_count += 1
        
        if (idx + 1) % 5000 == 0:
            print(f"Processed: {idx + 1:,} / {len(data):,} ({(idx + 1)/len(data)*100:.1f}%)")
    
    # Save to JSON
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    # Summary
    print("\n" + "="*60)
    print("PATCH WITH CROSS-DB LOOKUP - SUMMARY")
    print("="*60)
    print(f"Total records processed: {len(data):,}")
    print(f"Transactions patched: {patched_count:,}")
    print(f"  └─ Found in tt_jual_detail: {lookup_jual_count:,}")
    print(f"  └─ Found in tt_beli_detail: {lookup_beli_count:,}")
    print(f"Not found in both: {not_found_count:,}")
    print("="*60)
    print(f"\n✓ Output saved to: {output_file}")

if __name__ == "__main__":
    try:
        patch_kmt_with_cache()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
