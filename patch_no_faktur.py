from pymongo import ReadPreference
import json
from collections import defaultdict
from config import Config

def patch_no_faktur_with_cache():
    """
    Script untuk patch no_faktur di information_transaction dengan lookup ke tt_jual_detail
    menggunakan kode_barcode sebagai kunci lookup
    """
    # Load konfigurasi
    Config.print_config()
    
    # Input/output files
    input_file = 'tmsambassg.tt_member_transformed.json'
    output_file = 'tmsambassg.tt_member_no_faktur_patched.json'
    
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
        
        # Get database - SAMBAS (tmsambassg) bukan db_hdpayn_asli
        db_sambas = client['tmsambassg']
        
        # Get collection dengan read preference secondary
        tt_jual_detail = db_sambas['tt_jual_detail'].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        
        print("✓ Connected to MongoDB (tmsambassg) successfully")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return
    
    # Collect all unique kode_barcode yang perlu di-lookup
    print("\nCollecting kode_barcode to lookup...")
    barcode_set = set()
    
    for member in data:
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                if trans.get('no_faktur') == '-':
                    kode_barcode = trans.get('kode_barcode')
                    if kode_barcode and kode_barcode != '-':
                        barcode_set.add(kode_barcode)
    
    print(f"✓ Found {len(barcode_set):,} unique kode_barcode to lookup")
    
    # Build cache dari tt_jual_detail
    print("\nBuilding cache from tt_jual_detail...")
    jual_cache = {}
    barcode_list = list(barcode_set)
    batch_size = 1000
    
    for i in range(0, len(barcode_list), batch_size):
        batch = barcode_list[i:i+batch_size]
        results = tt_jual_detail.find(
            {"kode_barcode": {"$in": batch}, "no_faktur_jual": {"$ne": "-"}},
            {"kode_barcode": 1, "no_faktur_jual": 1, "nama_barang": 1, "berat": 1}
        )
        
        for doc in results:
            kode_barcode = doc.get('kode_barcode')
            # Simpan dalam cache, gunakan list jika ada multiple faktur untuk 1 barcode
            if kode_barcode not in jual_cache:
                jual_cache[kode_barcode] = []
            
            jual_cache[kode_barcode].append({
                'no_faktur_jual': doc.get('no_faktur_jual', '-'),
                'nama_barang': doc.get('nama_barang', '-'),
                'berat': doc.get('berat', 0)
            })
        
        if (i + batch_size) % 10000 == 0:
            print(f"Loaded: {min(i + batch_size, len(barcode_list)):,} / {len(barcode_list):,}")
    
    print(f"✓ Cached {len(jual_cache):,} barcodes from tt_jual_detail")
    
    # Close database connection
    client.close()
    
    # Patch data menggunakan cache
    print("\nPatching data using cache...")
    print("="*60)
    
    patched_count = 0
    not_found_count = 0
    already_filled_count = 0
    no_barcode_count = 0
    
    for idx, member in enumerate(data):
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                # Hanya proses jika no_faktur adalah "-"
                if trans.get('no_faktur') == '-':
                    kode_barcode = trans.get('kode_barcode')
                    
                    if not kode_barcode or kode_barcode == '-':
                        no_barcode_count += 1
                        continue
                    
                    # Check cache
                    if kode_barcode in jual_cache:
                        # Ambil data pertama dari list (jika ada multiple)
                        jual_data = jual_cache[kode_barcode][0]
                        
                        # Update no_faktur dengan no_faktur_jual dari tt_jual_detail
                        trans['no_faktur'] = jual_data['no_faktur_jual']
                        
                        # Bonus: update nama_barang jika masih "-" atau "8F"
                        if trans.get('nama_barang') in ['-', '8F'] and jual_data['nama_barang'] != '-':
                            trans['nama_barang'] = jual_data['nama_barang']
                        
                        # Bonus: update berat jika 0 atau tidak ada
                        if not trans.get('berat') or trans.get('berat') == 0:
                            if jual_data['berat']:
                                trans['berat'] = jual_data['berat']
                        
                        trans['lookup_source'] = 'tt_jual_detail'
                        patched_count += 1
                    else:
                        not_found_count += 1
                else:
                    already_filled_count += 1
        
        # Progress indicator
        if (idx + 1) % 1000 == 0:
            print(f"Processed: {idx + 1:,} / {len(data):,}")
    
    # Save patched data
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("PATCH NO_FAKTUR - SUMMARY")
    print("="*60)
    print(f"Total records processed: {len(data):,}")
    print(f"Records patched: {patched_count:,}")
    print(f"Records already have no_faktur: {already_filled_count:,}")
    print(f"Records without kode_barcode: {no_barcode_count:,}")
    print(f"Records not found in tt_jual_detail: {not_found_count:,}")
    print("="*60)
    print(f"\n✓ Output saved to: {output_file}")

if __name__ == "__main__":
    try:
        patch_no_faktur_with_cache()
        print("\n✓ Data patching complete!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
