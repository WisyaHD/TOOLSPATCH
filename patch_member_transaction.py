import json

def patch_member_data(input_file, output_file):
    """
    Script untuk mem-patch data member dengan menambahkan information_transaction
    berdasarkan field 'berat' jika belum ada.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    patched_count = 0
    skipped_count = 0
    error_count = 0
    
    for item in data:
        # Skip jika "information_transaction" sudah ada
        if "information_transaction" in item and item["information_transaction"]:
            skipped_count += 1
            continue
        
        # Proses jika "information_transaction" belum ada atau kosong
        berat_value = item.get("berat", "-")
        
        # Skip jika berat adalah "-" atau kosong
        if berat_value == "-" or berat_value == "" or berat_value is None:
            error_count += 1
            continue
        
        # Coba konversi berat ke float
        try:
            if isinstance(berat_value, str):
                berat_float = float(berat_value)
            else:
                berat_float = float(berat_value)
            
            # Buat information_transaction dengan struktur minimal
            item["information_transaction"] = [
                {
                    "berat": berat_float,
                    "nama_barang": item.get("deskripsi", "-"),
                    "nama_atribut": "-",
                    "no_faktur": item.get("deskripsi", "-"),
                    "kadar": 0,
                    "kadar_cetak": "-",
                    "kadar_modal": 0,
                    "kode_barcode": "-",
                    "kode_dept": "-",
                    "kode_group": "-",
                    "harga": int(item.get("jumlah_rp", 0)) if item.get("jumlah_rp") else 0
                }
            ]
            patched_count += 1
            
        except (ValueError, TypeError) as e:
            # Handle jika berat tidak bisa dikonversi ke float
            print(f"Error processing item {item.get('no_trx', 'unknown')}: {e}")
            error_count += 1
            continue
    
    # Simpan hasil ke file output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("PATCH MEMBER DATA - SUMMARY")
    print("="*60)
    print(f"Total records processed: {len(data)}")
    print(f"Records patched: {patched_count}")
    print(f"Records skipped (already have information_transaction): {skipped_count}")
    print(f"Records with error/invalid berat: {error_count}")
    print("="*60)
    print(f"\nOutput saved to: {output_file}")

if __name__ == "__main__":
    input_file = 'tt_member.json'
    output_file = 'tt_member_patched.json'
    
    try:
        patch_member_data(input_file, output_file)
        print("\n✓ Data transformation complete!")
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found!")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{input_file}'!")
    except Exception as e:
        print(f"Error: {e}")
