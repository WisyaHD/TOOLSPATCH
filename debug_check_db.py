import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Load members
with open('tt_member123.json') as f:
    members = json.load(f)

# Collect sample no_faktur_jual
sample_no_fakturs = []
for member in members[:100]:
    if member.get('kategori') == 'B278C07EC8B1C1B57F':
        deskripsi = member.get('deskripsi', '')
        kode_toko = member.get('kode_toko', '')
        if deskripsi and '-' in deskripsi:
            sample_no_fakturs.append({
                'deskripsi': deskripsi,
                'kode_toko': kode_toko
            })
        if len(sample_no_fakturs) >= 10:
            break

print("Sample no_faktur_jual to lookup:")
for sample in sample_no_fakturs:
    print(f"  {sample['kode_toko']}: {sample['deskripsi']}")

# Connect to MongoDB
mongo_uri = os.getenv('MONGODB_CONNECTION_STRING')
client = MongoClient(mongo_uri)

# Check db_hdpkmt for KM- prefix
db = client['db_hdpkmt']
collection = db['tt_jual_detail']

print("\n=== Checking db_hdpkmt (KMT) ===")
# Check total documents
try:
    total = collection.count_documents({})
    print(f"Total documents: {total}")
    
    # Get one sample
    if total > 0:
        sample = collection.find_one()
        print(f"\nSample document structure:")
        print(f"  no_faktur_jual: {sample.get('no_faktur_jual')}")
        print(f"  kode_barcode: {sample.get('kode_barcode')}")
        print(f"  _id: {sample.get('_id')}")
        
        # Check if any of our sample no_faktur exists
        print(f"\n=== Checking sample no_faktur_jual ===")
        for sample_item in sample_no_fakturs[:3]:
            if sample_item['kode_toko'] == 'KMT':
                result = collection.find_one({'no_faktur_jual': sample_item['deskripsi']})
                print(f"{sample_item['deskripsi']}: {'FOUND' if result else 'NOT FOUND'}")
                
        # Try to find any KM- prefix
        print("\n=== Looking for any KM- prefix ===")
        km_sample = collection.find_one({'no_faktur_jual': {'$regex': '^KM-'}})
        if km_sample:
            print(f"Found: {km_sample.get('no_faktur_jual')}")
        else:
            print("No KM- prefix found")
            
except Exception as e:
    print(f"Error: {str(e)}")
