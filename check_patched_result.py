import json

# Cek sample dari file hasil patch
INPUT_FILE = "tt_member-1_patched.json"

print("=" * 80)
print("Cek File Hasil Patch")
print("=" * 80)
print()

print(f"Loading {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    members = json.load(f)

print(f"Total members: {len(members)}")
print()

TARGET_CATEGORY = "B278C07EC8B1C1B57F"

# Cari member dengan kategori target
found_samples = 0
for member in members:
    if member.get("kategori") != TARGET_CATEGORY:
        continue
    
    info_trans = member.get("information_transaction", [])
    if not isinstance(info_trans, list) or len(info_trans) == 0:
        continue
    
    print(f"Sample #{found_samples + 1}:")
    print(f"  Kode Toko: {member.get('kode_toko', 'N/A')}")
    print(f"  Member ID: {member.get('_id', {}).get('$oid', 'N/A')}")
    print(f"  Total Transactions: {len(info_trans)}")
    print(f"  First Transaction:")
    trans = info_trans[0]
    for key in ["nama_barang", "no_faktur", "kode_group", "nama_atribut", "kadar", "kadar_modal", "kode_barcode", "kode_dept", "no_faktur_jual", "deskripsi", "berat", "harga"]:
        if key in trans:
            print(f"    {key}: {trans[key]}")
    print()
    
    found_samples += 1
    if found_samples >= 5:
        break

if found_samples == 0:
    print("Tidak ada member dengan kategori target ditemukan")

print("=" * 80)
