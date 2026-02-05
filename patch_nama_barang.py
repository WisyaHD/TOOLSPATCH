import json

def patch_nama_barang(input_file, output_file):
    """
    Script untuk mem-patch nama_barang di dalam information_transaction
    agar sesuai dengan nama_barang yang ada di luar array.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    patched_count = 0
    skipped_count = 0
    no_info_trans = 0
    no_nama_barang = 0
    
    for item in data:
        # Skip jika tidak ada information_transaction
        if "information_transaction" not in item or not item["information_transaction"]:
            no_info_trans += 1
            continue
        
        # Skip jika tidak ada nama_barang di luar array
        if "nama_barang" not in item or not item["nama_barang"] or item["nama_barang"] == "-":
            no_nama_barang += 1
            continue
        
        # Ambil nama_barang dari luar array
        nama_barang_luar = item["nama_barang"]
        
        # Update semua nama_barang di dalam information_transaction
        updated = False
        for trans in item["information_transaction"]:
            # Cek apakah nama_barang berbeda
            if trans.get("nama_barang") != nama_barang_luar:
                trans["nama_barang"] = nama_barang_luar
                updated = True
        
        if updated:
            patched_count += 1
        else:
            skipped_count += 1
    
    # Simpan hasil ke file output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("PATCH NAMA BARANG - SUMMARY")
    print("="*60)
    print(f"Total records processed: {len(data)}")
    print(f"Records patched: {patched_count}")
    print(f"Records skipped (already same): {skipped_count}")
    print(f"Records without information_transaction: {no_info_trans}")
    print(f"Records without nama_barang: {no_nama_barang}")
    print("="*60)
    print(f"\nOutput saved to: {output_file}")

if __name__ == "__main__":
    input_file = 'db_hdpayn_asli.tt_member18.json'
    output_file = 'db_hdpayn_asli.tt_member_patched.json'
    
    try:
        patch_nama_barang(input_file, output_file)
        print("\n✓ Patch nama_barang complete!")
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found!")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{input_file}'!")
    except Exception as e:
        print(f"Error: {e}")
