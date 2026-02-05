from pymongo import ReadPreference
import json
from config import Config
from collections import defaultdict

def patch_by_category():
    """
    Script untuk patch kode_barcode berdasarkan kategori dengan lookup ke collection yang sesuai:
    - A474C675BF90B7B97DB1 (BATAL BELI) → tt_beli_detail
    - A474C675BF90C5B97FB288B380B4BE (BATAL PENJUALAN) → tt_jual_detail
    - AA88C675C1B7 → tt_hutang_detail
    """
    # Load konfigurasi
    Config.print_config()
    
    # Koneksi ke MongoDB
    print("\nConnecting to MongoDB...")
    try:
        client = Config.get_mongodb_client()
        
        # Get databases
        db_member = client[Config.DB_MEMBER]
        db_jual = client[Config.DB_JUAL]
        db_beli = client[Config.DB_BELI]
        
        # Get collections dengan read preference secondary
        tt_jual_detail = db_jual[Config.COLLECTION_TT_JUAL_DETAIL].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        tt_beli_detail = db_beli[Config.COLLECTION_TT_BELI_DETAIL].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        tt_hutang_detail = db_member[Config.COLLECTION_TT_HUTANG_DETAIL].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        
        print("✓ Connected to MongoDB successfully")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        return
    
    # Load JSON file
    input_file = Config.JSON_TT_MEMBER
    print(f"\nLoading {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            tt_member_data = json.load(f)
        print(f"✓ Loaded {len(tt_member_data):,} records")
    except Exception as e:
        print(f"✗ Failed to load JSON: {e}")
        return
    
    print("\n" + "="*60)
    print("KATEGORI MAPPING")
    print("="*60)
    print("B278BF76B8BCBEB57F (PEMBELIAN) → tt_beli_detail")
    print("A474C675BF90B7B97DB1 (BATAL BELI) → tt_beli_detail")
    print("A474C675BF90C5B97FB288B380B4BE (BATAL PENJUALAN) → tt_jual_detail")
    print("AA88C675C1B7 → tt_hutang_detail")
    print("="*60)
    
    # Kumpulkan semua no_faktur per kategori
    print("\nCollecting no_faktur by category...")
    faktur_by_category = {
        'batal_beli': set(),
        'batal_jual': set(),
        'hutang': set()
    }
    
    for member in tt_member_data:
        kategori = member.get('kategori', '')
        
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                if trans.get('kode_barcode') == '-':
                    no_faktur = trans.get('no_faktur')
                    if no_faktur:
                        # PEMBELIAN dan BATAL BELI → tt_beli_detail
                        if kategori in ['A474C675BF90B7B97DB1', 'B278BF76B8BCBEB57F']:
                            faktur_by_category['batal_beli'].add(no_faktur)
                        elif kategori == 'A474C675BF90C5B97FB288B380B4BE':  # BATAL PENJUALAN
                            faktur_by_category['batal_jual'].add(no_faktur)
                        elif kategori == 'AA88C675C1B7':  # HUTANG
                            faktur_by_category['hutang'].add(no_faktur)
    
    print(f"BATAL BELI: {len(faktur_by_category['batal_beli']):,} unique faktur")
    print(f"BATAL PENJUALAN: {len(faktur_by_category['batal_jual']):,} unique faktur")
    print(f"HUTANG: {len(faktur_by_category['hutang']):,} unique faktur")
    
    # Build cache dari database
    print("\nBuilding cache from database...")
    cache_beli = {}
    cache_jual = {}
    cache_hutang = {}
    
    try:
        # Cache beli_detail
        if faktur_by_category['batal_beli']:
            print("Fetching tt_beli_detail...")
            cursor = tt_beli_detail.find(
                {
                    "no_faktur": {"$in": list(faktur_by_category['batal_beli'])},
                    "kode_barcode": {"$ne": "-"}
                },
                {"no_faktur": 1, "kode_barcode": 1, "nama_barang": 1}
            ).batch_size(1000)
            
            for doc in cursor:
                no_faktur = doc.get('no_faktur')
                if no_faktur not in cache_beli:
                    cache_beli[no_faktur] = []
                cache_beli[no_faktur].append({
                    'kode_barcode': doc.get('kode_barcode'),
                    'nama_barang': doc.get('nama_barang')
                })
            print(f"  ✓ Cached {len(cache_beli):,} faktur from tt_beli_detail")
        
        # Cache jual_detail
        if faktur_by_category['batal_jual']:
            print("Fetching tt_jual_detail...")
            cursor = tt_jual_detail.find(
                {
                    "no_faktur": {"$in": list(faktur_by_category['batal_jual'])},
                    "kode_barcode": {"$ne": "-"}
                },
                {"no_faktur": 1, "kode_barcode": 1, "nama_barang": 1}
            ).batch_size(1000)
            
            for doc in cursor:
                no_faktur = doc.get('no_faktur')
                if no_faktur not in cache_jual:
                    cache_jual[no_faktur] = []
                cache_jual[no_faktur].append({
                    'kode_barcode': doc.get('kode_barcode'),
                    'nama_barang': doc.get('nama_barang')
                })
            print(f"  ✓ Cached {len(cache_jual):,} faktur from tt_jual_detail")
        
        # Cache hutang_detail
        if faktur_by_category['hutang']:
            print("Fetching tt_hutang_detail...")
            cursor = tt_hutang_detail.find(
                {
                    "no_faktur": {"$in": list(faktur_by_category['hutang'])},
                    "kode_barcode": {"$ne": "-"}
                },
                {"no_faktur": 1, "kode_barcode": 1, "nama_barang": 1}
            ).batch_size(1000)
            
            for doc in cursor:
                no_faktur = doc.get('no_faktur')
                if no_faktur not in cache_hutang:
                    cache_hutang[no_faktur] = []
                cache_hutang[no_faktur].append({
                    'kode_barcode': doc.get('kode_barcode'),
                    'nama_barang': doc.get('nama_barang')
                })
            print(f"  ✓ Cached {len(cache_hutang):,} faktur from tt_hutang_detail")
        
    except Exception as e:
        print(f"Error building cache: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        client.close()
    
    # Patch data
    print("\nPatching data using cache...")
    patched_count = 0
    patched_beli = 0
    patched_jual = 0
    patched_hutang = 0
    
    for member in tt_member_data:
        kategori = member.get('kategori', '')
        
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                if trans.get('kode_barcode') == '-':
                    no_faktur = trans.get('no_faktur')
                    
                    if no_faktur:
                        lookup_result = None
                        source = None
                        
                        # Tentukan cache berdasarkan kategori
                        # PEMBELIAN dan BATAL BELI → tt_beli_detail
                        if kategori in ['A474C675BF90B7B97DB1', 'B278BF76B8BCBEB57F']:
                            lookup_result = cache_beli.get(no_faktur)
                            source = 'tt_beli_detail'
                            if lookup_result:
                                patched_beli += 1
                        elif kategori == 'A474C675BF90C5B97FB288B380B4BE':  # BATAL PENJUALAN
                            lookup_result = cache_jual.get(no_faktur)
                            source = 'tt_jual_detail'
                            if lookup_result:
                                patched_jual += 1
                        elif kategori == 'AA88C675C1B7':  # HUTANG
                            lookup_result = cache_hutang.get(no_faktur)
                            source = 'tt_hutang_detail'
                            if lookup_result:
                                patched_hutang += 1
                        
                        # Update jika ditemukan
                        if lookup_result and len(lookup_result) > 0:
                            result = lookup_result[0]
                            new_barcode = result.get('kode_barcode', '-')
                            
                            # Hanya update jika kode_barcode hasil lookup BUKAN "-"
                            if new_barcode and new_barcode != '-':
                                trans['kode_barcode'] = new_barcode
                                if result.get('nama_barang'):
                                    trans['nama_barang'] = result.get('nama_barang')
                                trans['lookup_source'] = source
                                patched_count += 1
                            else:
                                # Jika hasil lookup masih "-", isi dengan "-" saja
                                trans['kode_barcode'] = '-'
    
    # Save hasil
    output_file = 'kmt1.tt_member_patched.json'
    print(f"\nSaving to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tt_member_data, f, indent=2, ensure_ascii=False, default=str)
    
    # Summary
    print("\n" + "="*60)
    print("PATCH BY CATEGORY - SUMMARY")
    print("="*60)
    print(f"Total transactions patched: {patched_count:,}")
    print(f"  - From tt_beli_detail (PEMBELIAN + BATAL BELI): {patched_beli:,}")
    print(f"  - From tt_jual_detail (BATAL PENJUALAN): {patched_jual:,}")
    print(f"  - From tt_hutang_detail: {patched_hutang:,}")
    print("="*60)
    print(f"\n✓ Output saved to: {output_file}")

if __name__ == "__main__":
    try:
        patch_by_category()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
