"""
Script to extract unique product-weight-size mappings from Excel files
and populate the product_mapping database table.
"""
import pandas as pd
from app import app
from database import db, ProductMapping
import os
from glob import glob

def extract_and_populate_product_mapping(excel_files):
    """
    Extract unique product name, box weight, and box size from Excel files
    and populate the database.
    """
    all_products = []

    for file_path in excel_files:
        try:
            df = pd.read_excel(file_path)

            # Extract relevant columns: 品名, 箱重量, 箱尺寸
            if all(col in df.columns for col in ['品名', '箱重量', '箱尺寸']):
                # Drop rows where product name is missing
                product_data = df[['品名', '箱重量', '箱尺寸']].dropna(subset=['品名'])
                all_products.append(product_data)
            else:
                print(f"Warning: Required columns not found in {file_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    if not all_products:
        print("No product data found in any files")
        return

    # Combine all product data
    combined_df = pd.concat(all_products, ignore_index=True)

    # Group by product name and take the first non-null weight/size for each product
    # This handles cases where the same product might appear multiple times
    unique_products = combined_df.groupby('品名').agg({
        '箱重量': lambda x: x.dropna().iloc[0] if not x.dropna().empty else None,
        '箱尺寸': lambda x: x.dropna().iloc[0] if not x.dropna().empty else None
    }).reset_index()

    print(f"\nFound {len(unique_products)} unique products")

    # Populate database
    with app.app_context():
        added_count = 0
        updated_count = 0
        skipped_count = 0

        for _, row in unique_products.iterrows():
            product_name = str(row['品名']).strip()
            box_weight = row['箱重量']
            box_size = row['箱尺寸']

            # Convert box_weight to float if possible
            try:
                box_weight = float(box_weight) if pd.notna(box_weight) else None
            except (ValueError, TypeError):
                box_weight = None

            # Convert box_size to string if not null
            box_size = str(box_size).strip() if pd.notna(box_size) else None

            # Check if product already exists
            existing = ProductMapping.query.filter_by(product_name=product_name).first()

            if existing:
                # Update if new data has values and existing doesn't
                updated = False
                if box_weight is not None and existing.box_weight is None:
                    existing.box_weight = box_weight
                    updated = True
                if box_size is not None and existing.box_size is None:
                    existing.box_size = box_size
                    updated = True

                if updated:
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                # Add new product mapping
                new_mapping = ProductMapping(
                    product_name=product_name,
                    box_weight=box_weight,
                    box_size=box_size
                )
                db.session.add(new_mapping)
                added_count += 1

        db.session.commit()

        print(f"\nResults:")
        print(f"  - Added: {added_count} new products")
        print(f"  - Updated: {updated_count} existing products")
        print(f"  - Skipped: {skipped_count} (already complete)")
        print(f"\nTotal products in database: {ProductMapping.query.count()}")

if __name__ == '__main__':
    # Find all Excel files in uploads folder
    upload_folder = '/Users/na/Report/uploads'
    excel_files = glob(os.path.join(upload_folder, '*.xlsx'))

    print(f"Found {len(excel_files)} Excel files in {upload_folder}")

    if excel_files:
        extract_and_populate_product_mapping(excel_files)
    else:
        print("No Excel files found to process")
