from pymongo import ReadPreference
import json
from config import Config

def check_sample_data():
    """Script untuk cek sample data dan verifikasi lookup"""
    
    Config.print_config()
    
    # Load JSON
    print("\nLoading kmt1.tt_member.json...")
    with open('kmt1.tt_member.json', 'r', encoding='utf-8') as f:
        tt_member_data = json.load(f)
    
    # Ambil sample no_faktur dari kategori PEMBELIAN
    sample_fakturs = []
    for member in tt_member_data[:100]:
        kategori = member.get('kategori', '')
        if kategori in ['B278BF76B8BCBEB57F', 'A474C675BF90B7B97DB1']:
            if 'information_transaction' in member:
                for trans in member['information_transaction']:
                    if trans.get('kode_barcode') == '-':
                        no_faktur = trans.get('no_faktur')
                        if no_faktur:
                            sample_fakturs.append(no_faktur)
                            if len(sample_fakturs) >= 10:
                                break
        if len(sample_fakturs) >= 10:
            break
    
    print(f"\nSample no_faktur dari kmt1.tt_member.json:")
    for i, fak in enumerate(sample_fakturs[:5], 1):
        print(f"{i}. {fak}")
    
    # Connect ke database
    print("\nConnecting to database...")
    client = Config.get_mongodb_client()
    db_beli = client[Config.DB_BELI]
    tt_beli_detail = db_beli[Config.COLLECTION_TT_BELI_DETAIL].with_options(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )
    
    print(f"\nChecking if these faktur exist in tt_beli_detail...")
    for fak in sample_fakturs[:5]:
        # Cek apakah faktur ada di database
        count_all = tt_beli_detail.count_documents({"no_faktur": fak})
        count_with_barcode = tt_beli_detail.count_documents({
            "no_faktur": fak,
            "kode_barcode": {"$ne": "-"}
        })
        
        print(f"\n{fak}:")
        print(f"  Total records in tt_beli_detail: {count_all}")
        print(f"  With kode_barcode != '-': {count_with_barcode}")
        
        if count_all > 0:
            # Tampilkan sample
            sample = tt_beli_detail.find_one({"no_faktur": fak})
            print(f"  Sample barcode: {sample.get('kode_barcode', 'N/A')}")
    
    # Cek total data di tt_beli_detail
    print(f"\n{'='*60}")
    print("Database Statistics:")
    total_beli = tt_beli_detail.count_documents({})
    total_with_barcode = tt_beli_detail.count_documents({"kode_barcode": {"$ne": "-"}})
    print(f"Total records in tt_beli_detail: {total_beli:,}")
    print(f"Records with kode_barcode != '-': {total_with_barcode:,}")
    
    client.close()

if __name__ == "__main__":
    check_sample_data()
