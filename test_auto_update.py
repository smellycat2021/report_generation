#!/usr/bin/env python3
"""
Test script to verify auto-update functionality for product mappings.
"""

from database import db, ProductMapping
from app import app
from data_processor import process_manufacturer_data
import os

def test_auto_update():
    with app.app_context():
        # Check current count
        before_count = ProductMapping.query.count()
        print(f'📊 Before processing:')
        print(f'   Total products in database: {before_count}')

        # Get sample of current data
        sample = ProductMapping.query.limit(5).all()
        print(f'\n   Sample products:')
        for p in sample:
            print(f'   - {p.product_name}: weight={p.box_weight}, size={p.box_size}')

        # Find a test file
        uploads_dir = 'uploads'
        test_files = [f for f in os.listdir(uploads_dir) if f.endswith(('.xlsx', '.xls'))]

        if not test_files:
            print('\n❌ No test files found in uploads/ directory')
            return

        test_file = os.path.join(uploads_dir, test_files[0])
        print(f'\n🔄 Processing test file: {test_files[0]}')
        print()

        # Process the file
        result = process_manufacturer_data([test_file], {})

        # Check after count
        after_count = ProductMapping.query.count()
        print(f'\n📊 After processing:')
        print(f'   Total products in database: {after_count}')
        print(f'   Change: +{after_count - before_count}')

        # Show some updated products
        print(f'\n   Recently updated/created products:')
        recent = ProductMapping.query.order_by(ProductMapping.updated_at.desc()).limit(5).all()
        for p in recent:
            print(f'   - {p.product_name}: weight={p.box_weight}, size={p.box_size}')

if __name__ == '__main__':
    test_auto_update()
