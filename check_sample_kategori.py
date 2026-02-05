import json

# Load file
with open("tt_member-1.json", 'r', encoding='utf-8') as f:
    members = json.load(f)

# Filter by kategori
target_kategori = "B278C07EC8B1C1B57F"
filtered = [m for m in members if m.get("kategori") == target_kategori]

print(f"Total members dengan kategori {target_kategori}: {len(filtered)}")
print()

if len(filtered) > 0:
    # Ambil sample pertama
    sample = filtered[0]
    
    print("=" * 80)
    print("SAMPLE DATA #1:")
    print("=" * 80)
    print(f"Kode Toko: {sample.get('kode_toko')}")
    print(f"No Faktur Jual: {sample.get('no_faktur_jual')}")
    print(f"Deskripsi: {sample.get('deskripsi')}")
    print()
    
    if "information_transaction" in sample:
        print("Information Transaction:")
        for i, trans in enumerate(sample["information_transaction"][:3]):  # Ambil 3 item pertama
            print(f"\n  Item #{i+1}:")
            for key, value in trans.items():
                print(f"    {key}: {value}")
    
    print("\n" + "=" * 80)
    
    # Cek berapa banyak yang punya information_transaction dengan semua field "-" atau 0
    count_empty = 0
    for member in filtered[:100]:  # Cek 100 sample pertama
        if "information_transaction" in member:
            for trans in member["information_transaction"]:
                if (trans.get("nama_barang") == "-" and
                    trans.get("no_faktur") == "-" and
                    trans.get("kode_group") == "-" and
                    trans.get("nama_atribut") == "-" and
                    trans.get("kadar") == 0 and
                    trans.get("kadar_modal") == 0 and
                    trans.get("kode_barcode") == "-" and
                    trans.get("kode_dept") == "-"):
                    count_empty += 1
    
    print(f"\nDari 100 sample pertama:")
    print(f"Jumlah transaction items yang match kondisi (semua field kosong): {count_empty}")
