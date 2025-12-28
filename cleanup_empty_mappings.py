#!/usr/bin/env python3
"""
Cleanup script to remove product mappings that have no weight/size information.
Deletes rows where both box_weight and box_size are NULL.
"""

from database import db, ProductMapping
from app import app

def cleanup_empty_mappings():
    """Remove product mappings with no weight/size data"""
    with app.app_context():
        # Count before deletion
        total_before = ProductMapping.query.count()
        empty_count = ProductMapping.query.filter(
            (ProductMapping.box_weight == None) & (ProductMapping.box_size == None)
        ).count()

        print(f"📊 Current Statistics:")
        print(f"   Total products: {total_before}")
        print(f"   Products with data: {total_before - empty_count}")
        print(f"   Products with NO data: {empty_count}")
        print()

        if empty_count == 0:
            print("✅ No empty mappings to clean up!")
            return

        # Ask for confirmation
        response = input(f"⚠️  Are you sure you want to delete {empty_count} empty product mappings? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Cleanup cancelled.")
            return

        # Delete empty mappings
        deleted = ProductMapping.query.filter(
            (ProductMapping.box_weight == None) & (ProductMapping.box_size == None)
        ).delete()

        db.session.commit()

        # Count after deletion
        total_after = ProductMapping.query.count()

        print()
        print(f"✅ Cleanup completed!")
        print(f"   Deleted: {deleted} product mappings")
        print(f"   Remaining: {total_after} products with weight/size data")

if __name__ == '__main__':
    cleanup_empty_mappings()
