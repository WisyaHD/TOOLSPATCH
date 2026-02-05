from pymongo import ReadPreference
from config import Config

# Connect
client = Config.get_mongodb_client()
db_beli = client[Config.DB_BELI]
tt_beli_detail = db_beli[Config.COLLECTION_TT_BELI_DETAIL].with_options(
    read_preference=ReadPreference.SECONDARY_PREFERRED
)

# Test query
test_faktur = "KMT-PI22-03349"
result = tt_beli_detail.find_one({"no_faktur": test_faktur})

print(f"Searching for: {test_faktur}")
print(f"Result: {result}")

# Count total
total = tt_beli_detail.count_documents({})
print(f"\nTotal records in tt_beli_detail: {total:,}")

# Sample dengan kode_barcode
sample = list(tt_beli_detail.find({"kode_barcode": {"$ne": "-"}}).limit(3))
print(f"\nSample with kode_barcode != '-':")
for s in sample:
    print(f"  No Faktur: {s.get('no_faktur')}, Barcode: {s.get('kode_barcode')}")

client.close()
