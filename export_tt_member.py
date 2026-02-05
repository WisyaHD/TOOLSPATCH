from pymongo import MongoClient, ReadPreference
import json
from datetime import datetime
from config import Config

def patch_kode_barcode_no_lookup():
    """
    Script untuk mem-patch kode_barcode di information_transaction
    TANPA lookup, hanya membaca dari tt_member saja
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
        
        # Test connection dengan count (bisa dari secondary)
        count = tt_member.count_documents({}, limit=1)
        print("✓ Connected to MongoDB successfully")
        print(f"✓ Can read from database")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        return
    
    print("\nStarting patch process...")
    print("="*60)
    
    # Query sederhana tanpa lookup - hanya filter di tt_member
    query = {
        "deskripsi": {"$regex": "KM"},
        "information_transaction": {"$exists": True, "$ne": []},
        "information_transaction.kode_barcode": "-"
    }
    
    try:
        # Count total yang perlu di-patch
        total_found = tt_member.count_documents(query)
        print(f"Found {total_found:,} records matching criteria")
        
        if total_found == 0:
            print("No records to patch. Exiting...")
            return
        
        # Tampilkan sample 5 records
        print("\nSample records:")
        sample = list(tt_member.find(query).limit(5))
        for i, record in enumerate(sample):
            print(f"{i+1}. No Trx: {record.get('no_trx')}")
            print(f"   Deskripsi: {record.get('deskripsi')}")
            if 'information_transaction' in record:
                for trans in record['information_transaction']:
                    print(f"   - No Faktur: {trans.get('no_faktur')}, Barcode: {trans.get('kode_barcode')}")
        
        # Konfirmasi
        proceed = input(f"\nProceed to fetch {total_found:,} records? (yes/no): ")
        if proceed.lower() != 'yes':
            print("Patch cancelled.")
            return
        
        # Fetch data dengan batch untuk menghindari timeout
        batch_size = 1000
        print(f"\nFetching data in batches of {batch_size:,}...")
        
        cursor = tt_member.find(query).batch_size(batch_size)
        
        # Export ke JSON untuk diproses offline
        output_file = 'tt_member_to_patch.json'
        print(f"Exporting to {output_file}...")
        
        records = []
        count = 0
        for record in cursor:
            # Convert ObjectId to string
            if '_id' in record and hasattr(record['_id'], '__dict__'):
                record['_id'] = str(record['_id'])
            records.append(record)
            count += 1
            
            if count % batch_size == 0:
                print(f"Fetched: {count:,} / {total_found:,} ({count/total_found*100:.1f}%)")
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False, default=str)
        
        # Summary
        print("\n" + "="*60)
        print("EXPORT SUMMARY")
        print("="*60)
        print(f"Total records exported: {len(records):,}")
        print(f"Output file: {output_file}")
        print("="*60)
        print("\n✓ Export complete!")
        print("\nSekarang Anda bisa proses file JSON ini secara offline")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close connection
        client.close()

if __name__ == "__main__":
    try:
        patch_kode_barcode_no_lookup()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
