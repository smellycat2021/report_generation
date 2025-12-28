#!/usr/bin/env python3
"""
Rebuild ProductMapping table from Excel files.
Reads columns: 日文名字, 规格, 单件净重(kg)
Maps to: product_name, box_size, box_weight
"""

import pandas as pd
import os
from database import db, ProductMapping
from app import app

def rebuild_product_mapping():
    """Clear and rebuild ProductMapping table from Excel files"""

    with app.app_context():
        # Clear existing data
        print("🗑️  Clearing existing ProductMapping table...")
        ProductMapping.query.delete()
        db.session.commit()
        print("   ✅ Table cleared\n")

        uploads_dir = 'uploads'
        excel_files = sorted([f for f in os.listdir(uploads_dir) if f.endswith(('.xlsx', '.xls'))])

        if not excel_files:
            print("❌ No Excel files found in uploads/ directory")
            return

        print(f"📂 Found {len(excel_files)} Excel files\n")

        # Track statistics
        total_files = 0
        skipped_files = []
        total_rows = 0
        duplicates = []
        created_count = 0

        # Store all products to detect duplicates
        seen_products = {}

        for excel_file in excel_files:
            file_path = os.path.join(uploads_dir, excel_file)

            try:
                print(f"📄 Processing: {excel_file}")
                df = pd.read_excel(file_path)

                # Check for required columns
                required_cols = ['日文名字', '规格', '单件净重(kg)']
                missing_cols = [col for col in required_cols if col not in df.columns]

                if missing_cols:
                    print(f"   ⚠️  Missing columns: {missing_cols}")
                    print(f"   ❌ Skipping this file\n")
                    skipped_files.append((excel_file, missing_cols))
                    continue

                # Extract relevant columns
                data = df[required_cols].copy()

                # Remove rows with missing product name
                data = data.dropna(subset=['日文名字'])

                # Process each row
                file_created = 0
                file_duplicates = 0

                for _, row in data.iterrows():
                    total_rows += 1

                    product_name = str(row['日文名字']).strip()
                    box_size = str(row['规格']).strip() if pd.notna(row['规格']) else None
                    box_weight = float(row['单件净重(kg)']) if pd.notna(row['单件净重(kg)']) else None

                    # Skip if both size and weight are None
                    if box_size is None and box_weight is None:
                        continue

                    # Check for duplicates
                    if product_name in seen_products:
                        duplicates.append({
                            'product_name': product_name,
                            'first_file': seen_products[product_name],
                            'duplicate_file': excel_file,
                            'box_size': box_size,
                            'box_weight': box_weight
                        })
                        file_duplicates += 1
                        continue

                    # Create new product mapping
                    product = ProductMapping(
                        product_name=product_name,
                        box_size=box_size if box_size else None,
                        box_weight=box_weight if box_weight else None
                    )
                    db.session.add(product)
                    seen_products[product_name] = excel_file
                    file_created += 1
                    created_count += 1

                db.session.commit()
                print(f"   ✅ Created: {file_created}, Duplicates: {file_duplicates}\n")
                total_files += 1

            except Exception as e:
                print(f"   ❌ Error: {str(e)}\n")
                skipped_files.append((excel_file, str(e)))
                continue

        # Print summary
        print("=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"Total files processed: {total_files}")
        print(f"Total files skipped: {len(skipped_files)}")
        print(f"Total rows examined: {total_rows}")
        print(f"Products created: {created_count}")
        print(f"Duplicates found: {len(duplicates)}")

        # Show skipped files
        if skipped_files:
            print(f"\n⚠️  Skipped Files:")
            for filename, reason in skipped_files:
                if isinstance(reason, list):
                    print(f"   - {filename}: Missing columns {reason}")
                else:
                    print(f"   - {filename}: {reason}")

        # Show duplicates
        if duplicates:
            print(f"\n🔁 Duplicate Products Report:")
            print(f"   (These products appeared in multiple files - first occurrence kept)")
            print()
            for dup in duplicates[:20]:  # Show first 20
                print(f"   Product: {dup['product_name']}")
                print(f"     ✅ Kept from: {dup['first_file']}")
                print(f"     ❌ Ignored from: {dup['duplicate_file']}")
                print()

            if len(duplicates) > 20:
                print(f"   ... and {len(duplicates) - 20} more duplicates")

        # Final count
        final_count = ProductMapping.query.count()
        print(f"\n✅ Final ProductMapping table count: {final_count}")

        # Show sample products
        print(f"\n📦 Sample Products:")
        samples = ProductMapping.query.limit(10).all()
        for p in samples:
            print(f"   {p.product_name}")
            print(f"     Size: {p.box_size}")
            print(f"     Weight: {p.box_weight} kg")

if __name__ == '__main__':
    rebuild_product_mapping()
