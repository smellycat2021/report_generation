#!/usr/bin/env python3
"""
Database Initialization on Startup
Automatically populates database with default data if empty (for fresh PostgreSQL deployments)
"""

from app import app
from database import db, ProductMapping, BrandMapping, KnownProductName
import subprocess
import sys
import os

def init_database_if_empty():
    """
    Check if database is empty and initialize with default data if needed.
    This is crucial for PostgreSQL deployments where the database starts empty.
    """
    with app.app_context():
        try:
            # Check if tables exist and have data
            product_count = ProductMapping.query.count()
            brand_count = BrandMapping.query.count()
            known_count = KnownProductName.query.count()

            print(f"📊 Current database state:")
            print(f"   - Products: {product_count}")
            print(f"   - Brands: {brand_count}")
            print(f"   - Known Names: {known_count}")

            # Initialize if database is empty
            if product_count == 0 or brand_count == 0 or known_count == 0:
                print("\n⚠️  Database is empty or incomplete, initializing...")

                # Initialize brand mappings
                if brand_count == 0:
                    print("   → Initializing brand mappings...")
                    result = subprocess.run(['python', 'init_brand_mapping.py'],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print("   ✅ Brand mappings initialized")
                    else:
                        print(f"   ❌ Error: {result.stderr}")

                # Initialize known product names
                if known_count == 0:
                    print("   → Initializing known product names...")
                    result = subprocess.run(['python', 'init_known_names.py'],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print("   ✅ Known product names initialized")
                    else:
                        print(f"   ❌ Error: {result.stderr}")

                # Initialize product mappings from Excel files (if uploads folder has files)
                if product_count == 0 and os.path.exists('uploads') and os.listdir('uploads'):
                    print("   → Rebuilding product mappings from Excel files...")
                    result = subprocess.run(['python', 'rebuild_product_mapping.py'],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print("   ✅ Product mappings rebuilt")
                    else:
                        print(f"   ❌ Error: {result.stderr}")
                elif product_count == 0:
                    print("   ⚠️  No Excel files in uploads/ folder to rebuild product mappings")

                # Final count
                with app.app_context():
                    final_product_count = ProductMapping.query.count()
                    final_brand_count = BrandMapping.query.count()
                    final_known_count = KnownProductName.query.count()

                print(f"\n✅ Database initialization complete!")
                print(f"   - Products: {final_product_count}")
                print(f"   - Brands: {final_brand_count}")
                print(f"   - Known Names: {final_known_count}")
            else:
                print("✅ Database already populated, no initialization needed")

        except Exception as e:
            print(f"❌ Error during database initialization: {e}")
            sys.exit(1)

if __name__ == '__main__':
    init_database_if_empty()
