from pymongo import MongoClient, ReadPreference
import json
from datetime import datetime
from config import Config

def patch_kode_barcode():
    """
    Script untuk mem-patch kode_barcode di information_transaction
    berdasarkan lookup ke tt_jual_detail
    """
    # Load konfigurasi
    Config.print_config()
    
    # Koneksi ke MongoDB menggunakan config
    print("\nConnecting to MongoDB...")
    try:
        client = Config.get_mongodb_client()
        db = Config.get_database()
        
        # Set read preference ke secondary untuk membaca dari replica
        tt_member = db[Config.COLLECTION_TT_MEMBER].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        tt_jual_detail = db[Config.COLLECTION_TT_JUAL_DETAIL].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        
        # Test connection dengan count (bisa dari secondary)
        count = tt_member.count_documents({}, limit=1)
        print("✓ Connected to MongoDB successfully")
        print(f"✓ Can read from database (test count: {count})")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        return
    
    print("Starting patch process...")
    print("="*60)
    
    # Query untuk menemukan data yang perlu di-patch
    pipeline = [
        { "$match": { "deskripsi": { "$regex": "KM" } } },
        { "$unwind": "$information_transaction" },
        { "$match": { "information_transaction.kode_barcode": "-" } },
        {
            "$lookup": {
                "from": "tt_jual_detail",
                "localField": "information_transaction.no_faktur",
                "foreignField": "no_faktur",
                "as": "jual"
            }
        },
        { "$unwind": "$jual" },
        { "$match": { "jual.kode_barcode": { "$ne": "-" } } },
        {
            "$project": {
                "_id": 1,
                "member_id": "$_id",
                "no_faktur": "$information_transaction.no_faktur",
                "old_barcode": "$information_transaction.kode_barcode",
                "new_barcode": "$jual.kode_barcode",
                "info_index": { "$indexOfArray": ["$information_transaction", "$information_transaction"] }
            }
        }
    ]
    
    results = list(tt_member.aggregate(pipeline))
    total_found = len(results)
    
    print(f"Found {total_found} records to patch")
    print("="*60)
    
    if total_found == 0:
        print("No records to patch. Exiting...")
        return
    
    # Tampilkan sample 5 records
    print("\nSample records to be patched:")
    for i, record in enumerate(results[:5]):
        print(f"{i+1}. Member ID: {record['member_id']}")
        print(f"   No Faktur: {record['no_faktur']}")
        print(f"   Old Barcode: {record['old_barcode']} -> New Barcode: {record['new_barcode']}")
    
    # Konfirmasi
    proceed = input(f"\nProceed to patch {total_found} records? (yes/no): ")
    if proceed.lower() != 'yes':
        print("Patch cancelled.")
        return
    
    # Proses patching
    patched_count = 0
    error_count = 0
    
    print("\nPatching records...")
    
    for idx, record in enumerate(results):
        try:
            member_id = record['member_id']
            no_faktur = record['no_faktur']
            new_barcode = record['new_barcode']
            
            # Update kode_barcode di information_transaction yang sesuai
            result = tt_member.update_one(
                {
                    "_id": member_id,
                    "information_transaction.no_faktur": no_faktur,
                    "information_transaction.kode_barcode": "-"
                },
                {
                    "$set": {
                        "information_transaction.$[elem].kode_barcode": new_barcode
                    }
                },
                array_filters=[
                    {
                        "elem.no_faktur": no_faktur,
                        "elem.kode_barcode": "-"
                    }
                ]
            )
            
            if result.modified_count > 0:
                patched_count += 1
            
            # Progress indicator setiap 100 records
            if (idx + 1) % 100 == 0:
                print(f"Progress: {idx + 1}/{total_found} ({(idx + 1)/total_found*100:.1f}%)")
        
        except Exception as e:
            error_count += 1
            print(f"Error patching record {member_id}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("PATCH KODE BARCODE - SUMMARY")
    print("="*60)
    print(f"Total records found: {total_found}")
    print(f"Records successfully patched: {patched_count}")
    print(f"Errors: {error_count}")
    print("="*60)
    print("\n✓ Patch complete!")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    try:
        patch_kode_barcode()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
