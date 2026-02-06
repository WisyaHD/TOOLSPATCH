#!/usr/bin/env python3
"""
FINAL SCRIPT - Patch No Faktur
Otomatis membaca database mapping dari .env config
Versi: 2.0 (Final & Clean)
"""
from pymongo import ReadPreference
import json
import os
from collections import defaultdict
from config import Config
from dotenv import load_dotenv

load_dotenv()

def get_db_mapping():
    """Baca database mapping dari .env file"""
    mapping = {}
    
    # Scan .env untuk semua DB_JUAL_* entries
    for key, value in os.environ.items():
        if key.startswith('DB_JUAL_') and key != 'DB_JUAL':
            # DB_JUAL_SBP -> SBP
            kode_toko = key.replace('DB_JUAL_', '')
            if value:
                mapping[kode_toko] = value
    
    return mapping

def patch_no_faktur_final(input_file=None, output_file=None):
    """
    Script FINAL untuk patch no_faktur
    - Otomatis baca database mapping dari config
    - Optimized untuk file besar
    - Clean & simple
    """
    
    # Auto-detect input file
    if not input_file:
        possible_files = [
            'uploads/sambas_pwj_pst.tt_member_transformed_4.json',
            'sambas_pwj_pst.tt_member_transformed.json',
        ]
        for f in possible_files:
            if os.path.exists(f):
                input_file = f
                break
    
    if not input_file or not os.path.exists(input_file):
        print(f"✗ Input file not found: {input_file}")
        return
    
    if not output_file:
        output_file = input_file.replace('.json', '_PATCHED.json')
    
    Config.print_config()
    
    # Get database mapping from .env
    db_mapping = get_db_mapping()
    
    print("\n" + "="*70)
    print("DATABASE MAPPING (from .env)")
    print("="*70)
    if db_mapping:
        for kode, db in sorted(db_mapping.items()):
            print(f"  {kode}: {db}")
    else:
        print("  ⚠ No database mapping found in .env!")
        print("  Please configure in web UI: http://localhost:5002")
        return
    print("="*70)
    
    print(f"\n[1] Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    size_mb = os.path.getsize(input_file) / (1024*1024)
    print(f"✓ Loaded {len(data):,} records ({size_mb:.2f} MB)")
    
    print("\n[2] Connecting to MongoDB...")
    try:
        client = Config.get_mongodb_client()
        db_connections = {}
        
        # Connect ke semua database yang ada di mapping
        unique_dbs = set(db_mapping.values())
        for db_name in unique_dbs:
            try:
                db_connections[db_name] = client[db_name]
                db_connections[db_name]['tt_jual_detail'].count_documents({}, limit=1)
                print(f"  ✓ {db_name}")
            except Exception as e:
                print(f"  ✗ {db_name}: {e}")
        
        print("✓ Connected")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return
    
    print("\n[3] Collecting barcodes per kode_toko...")
    barcode_by_toko = defaultdict(set)
    
    for member in data:
        kode_toko = (member.get('kode_toko') or '').upper()
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                if trans.get('no_faktur') == '-':
                    kode_barcode = trans.get('kode_barcode')
                    if kode_barcode and kode_barcode != '-':
                        barcode_by_toko[kode_toko].add(kode_barcode)
    
    total_barcodes = sum(len(b) for b in barcode_by_toko.values())
    print(f"✓ {total_barcodes:,} unique barcodes across {len(barcode_by_toko)} kode_toko")
    
    print("\n[4] Building cache from tt_jual_detail...")
    jual_cache = defaultdict(lambda: defaultdict(dict))
    batch_size = 2000
    total_cached = 0
    
    for kode_toko, barcode_set in sorted(barcode_by_toko.items()):
        db_name = db_mapping.get(kode_toko)
        
        if not db_name or db_name not in db_connections:
            print(f"  ⚠ {kode_toko}: No database mapping")
            continue
        
        db = db_connections[db_name]
        tt_jual_detail = db['tt_jual_detail'].with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        
        print(f"  {kode_toko} ({db_name})...", end=' ')
        
        barcode_list = list(barcode_set)
        toko_cached = 0
        
        for i in range(0, len(barcode_list), batch_size):
            batch = barcode_list[i:i+batch_size]
            
            results = tt_jual_detail.find(
                {"kode_barcode": {"$in": batch}},
                {"kode_barcode": 1, "no_faktur": 1, "no_faktur_jual": 1, "nama_barang": 1, "berat": 1}
            )
            
            for doc in results:
                kode_barcode = doc.get('kode_barcode')
                if kode_barcode and kode_barcode not in jual_cache[kode_toko]:
                    no_faktur_value = doc.get('no_faktur_jual') or doc.get('no_faktur') or '-'
                    
                    jual_cache[kode_toko][kode_barcode] = {
                        'no_faktur_jual': no_faktur_value,
                        'nama_barang': doc.get('nama_barang', '-'),
                        'berat': doc.get('berat', 0),
                        'source_db': db_name
                    }
                    toko_cached += 1
                    total_cached += 1
        
        print(f"{toko_cached:,} found")
    
    print(f"\n✓ Total cached: {total_cached:,}")
    
    client.close()
    
    print("\n[5] Patching data...")
    stats = {
        'patched': 0,
        'already_filled': 0,
        'not_found': 0,
        'no_barcode': 0,
        'by_toko': defaultdict(int)
    }
    
    for idx, member in enumerate(data):
        kode_toko = (member.get('kode_toko') or '').upper()
        
        if 'information_transaction' in member:
            for trans in member['information_transaction']:
                if trans.get('no_faktur') == '-':
                    kode_barcode = trans.get('kode_barcode')
                    
                    if not kode_barcode or kode_barcode == '-':
                        stats['no_barcode'] += 1
                        continue
                    
                    if kode_toko in jual_cache and kode_barcode in jual_cache[kode_toko]:
                        jual_data = jual_cache[kode_toko][kode_barcode]
                        
                        trans['no_faktur'] = jual_data['no_faktur_jual']
                        trans['no_faktur_jual'] = jual_data['no_faktur_jual']
                        trans['lookup_source'] = 'tt_jual_detail'
                        trans['lookup_db'] = jual_data['source_db']
                        
                        stats['patched'] += 1
                        stats['by_toko'][kode_toko] += 1
                        
                        if trans.get('nama_barang') in ['-', '8F']:
                            if jual_data['nama_barang'] != '-':
                                trans['nama_barang'] = jual_data['nama_barang']
                        
                        if not trans.get('berat') or trans.get('berat') == 0:
                            if jual_data['berat']:
                                trans['berat'] = jual_data['berat']
                    else:
                        stats['not_found'] += 1
                else:
                    stats['already_filled'] += 1
        
        if (idx + 1) % 50000 == 0:
            print(f"  {(idx + 1) / len(data) * 100:.1f}% ({idx + 1:,}/{len(data):,})")
    
    print("\n[6] Saving output...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved to {output_file}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Records: {len(data):,}")
    print(f"\n✓ No_Faktur patched: {stats['patched']:,}")
    print(f"  By toko:")
    for toko in sorted(stats['by_toko'].keys()):
        print(f"    {toko}: {stats['by_toko'][toko]:,}")
    print(f"\n  Already filled: {stats['already_filled']:,}")
    print(f"  No barcode: {stats['no_barcode']:,}")
    print(f"  Not found in db: {stats['not_found']:,}")
    
    total_need_patch = stats['patched'] + stats['not_found']
    if total_need_patch > 0:
        coverage = (stats['patched'] / total_need_patch * 100)
        print(f"\n📊 Coverage: {coverage:.1f}% ({stats['patched']:,}/{total_need_patch:,})")
    
    print("="*70)
    print(f"\n✓ Output: {output_file}")
    return output_file

if __name__ == "__main__":
    import sys
    
    input_arg = sys.argv[1] if len(sys.argv) > 1 else None
    output_arg = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        print("\n🚀 FINAL PATCH NO FAKTUR v2.0\n")
        patch_no_faktur_final(input_arg, output_arg)
        print("\n✅ SUCCESS!")
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
