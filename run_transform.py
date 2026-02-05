#!/usr/bin/env python3
"""
Script untuk menjalankan transform dengan progress indicator
"""
import json
import sys
import os
from datetime import datetime

# Import transform function
from transform_arjuna_structure import transform_member_structure, ENABLE_DB_LOOKUP

INPUT_FILE = "tmsambassg.tt_member.json"
OUTPUT_FILE = "tmsambassg.tt_member_transformed_with_lookup.json"

def main():
    print(f"\n{'='*60}")
    print(f"🔄 Starting Transform with DB Lookup")
    print(f"{'='*60}")
    print(f"Input file:  {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"DB Lookup:   {'✅ ENABLED' if ENABLE_DB_LOOKUP else '❌ DISABLED'}")
    print(f"{'='*60}\n")
    
    # Check input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return False
    
    try:
        # Read input file
        print("📖 Reading input file...")
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            members = json.load(f)
        
        if not isinstance(members, list):
            members = [members]
        
        total = len(members)
        print(f"✅ Found {total} members\n")
        
        # Transform members
        transformed_members = []
        print("⚙️  Transforming members...")
        
        for idx, member in enumerate(members):
            # Show progress
            progress = int((idx + 1) / total * 100)
            bar_filled = int(progress / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            print(f"\r[{bar}] {progress}% ({idx + 1}/{total})", end='', flush=True)
            
            # Transform
            transformed = transform_member_structure(member)
            transformed_members.append(transformed)
        
        print("\n✅ Transform complete\n")
        
        # Write output file
        print("💾 Writing output file...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(transformed_members, f, ensure_ascii=False, indent=2)
        
        output_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"✅ Output file saved: {OUTPUT_FILE} ({output_size:.1f} MB)\n")
        
        # Show sample
        if transformed_members:
            print("📊 Sample transformed member:")
            print(f"   Name: {transformed_members[0].get('nama_customer', 'N/A')}")
            print(f"   Transactions: {len(transformed_members[0].get('information_transaction', []))}")
            if transformed_members[0].get('information_transaction'):
                sample_item = transformed_members[0]['information_transaction'][0]
                print(f"   Sample item: {sample_item.get('nama_barang')} ({sample_item.get('no_faktur')})")
        
        print(f"\n{'='*60}")
        print("✅ Transform completed successfully!")
        print(f"{'='*60}\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
