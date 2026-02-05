from pymongo import ReadPreference
import json
from config import Config

def export_with_cross_db_lookup():
    """
    Script untuk export data tt_member dengan lookup ke tt_jual_detail dan tt_beli_detail
    dari database yang berbeda (bisa sama atau beda database dalam 1 cluster)
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
        tt_member = db_member[Config.COLLECTION_TT_MEMBER].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        tt_jual_detail = db_jual[Config.COLLECTION_TT_JUAL_DETAIL].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        tt_beli_detail = db_beli[Config.COLLECTION_TT_BELI_DETAIL].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        
        # Test connection
        count = tt_member.count_documents({}, limit=1)
        print("✓ Connected to MongoDB successfully")
        print(f"✓ Database Member: {Config.DB_MEMBER}")
        print(f"✓ Database Jual: {Config.DB_JUAL}")
        print(f"✓ Database Beli: {Config.DB_BELI}")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        return
    
    print("\nStarting export with cross-database lookup...")
    print("="*60)
    
    # Query filter untuk tt_member
    query = {
        "deskripsi": {"$regex": "KM"},
        "information_transaction": {"$exists": True, "$ne": []},
        "information_transaction.kode_barcode": "-"
    }
    
    try:
        # Count total
        total_found = tt_member.count_documents(query)
        print(f"Found {total_found:,} tt_member records to process")
        
        if total_found == 0:
            print("No records found. Exiting...")
            return
        
        # Tampilkan sample
        print("\nSample records:")
        sample = list(tt_member.find(query).limit(3))
        for i, record in enumerate(sample):
            print(f"{i+1}. No Trx: {record.get('no_trx')}, Deskripsi: {record.get('deskripsi')[:50]}")
        
        # Konfirmasi
        proceed = input(f"\nProceed to export {total_found:,} records with lookup? (yes/no): ")
        if proceed.lower() != 'yes':
            print("Export cancelled.")
            return
        
        # Fetch data dengan batch
        batch_size = 500
        print(f"\nFetching and processing data in batches of {batch_size:,}...")
        
        cursor = tt_member.find(query).batch_size(batch_size)
        
        results = []
        count = 0
        lookup_jual_count = 0
        lookup_beli_count = 0
        
        for member in cursor:
            count += 1
            
            # Process information_transaction
            if 'information_transaction' in member:
                for trans in member['information_transaction']:
                    if trans.get('kode_barcode') == '-':
                        no_faktur = trans.get('no_faktur')
                        
                        if no_faktur:
                            # Lookup ke tt_jual_detail
                            jual = tt_jual_detail.find_one(
                                {"no_faktur": no_faktur, "kode_barcode": {"$ne": "-"}},
                                {"kode_barcode": 1, "nama_barang": 1}
                            )
                            
                            if jual:
                                trans['kode_barcode'] = jual.get('kode_barcode', '-')
                                trans['nama_barang'] = jual.get('nama_barang', trans.get('nama_barang', '-'))
                                trans['source'] = 'tt_jual_detail'
                                lookup_jual_count += 1
                            else:
                                # Jika tidak ada di jual, coba lookup ke tt_beli_detail
                                beli = tt_beli_detail.find_one(
                                    {"no_faktur": no_faktur, "kode_barcode": {"$ne": "-"}},
                                    {"kode_barcode": 1, "nama_barang": 1}
                                )
                                
                                if beli:
                                    trans['kode_barcode'] = beli.get('kode_barcode', '-')
                                    trans['nama_barang'] = beli.get('nama_barang', trans.get('nama_barang', '-'))
                                    trans['source'] = 'tt_beli_detail'
                                    lookup_beli_count += 1
            
            # Convert ObjectId to string
            if '_id' in member and hasattr(member['_id'], '__dict__'):
                member['_id'] = str(member['_id'])
            
            results.append(member)
            
            # Progress
            if count % 100 == 0:
                print(f"Processed: {count:,} / {total_found:,} ({count/total_found*100:.1f}%) | "
                      f"Lookup Jual: {lookup_jual_count:,} | Lookup Beli: {lookup_beli_count:,}")
        
        # Save to JSON
        output_file = 'tt_member_with_lookup.json'
        print(f"\nSaving to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Summary
        print("\n" + "="*60)
        print("EXPORT WITH CROSS-DB LOOKUP - SUMMARY")
        print("="*60)
        print(f"Total records processed: {len(results):,}")
        print(f"Found in tt_jual_detail: {lookup_jual_count:,}")
        print(f"Found in tt_beli_detail: {lookup_beli_count:,}")
        print(f"Total matched: {lookup_jual_count + lookup_beli_count:,}")
        print("="*60)
        print(f"\n✓ Output saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    try:
        export_with_cross_db_lookup()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
