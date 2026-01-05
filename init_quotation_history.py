#!/usr/bin/env python3
"""
Initialize Quotation History from Historical Files
Scans uploads/history/*.xlsx and imports to database.
"""

from app import app
from quotation_processor import read_historical_quotation
from database import db, QuotationHistory
import glob
import os
from datetime import datetime


def init_quotation_history():
    """
    Initialize quotation history table from historical quotation files.
    Scans uploads/history/ for YYYYMMDD.xlsx files and imports them.
    """
    with app.app_context():
        # Find all Excel files in uploads/history/
        history_pattern = os.path.join('uploads', 'history', '*.xlsx')
        history_files = glob.glob(history_pattern)

        if not history_files:
            print("⚠️  No historical quotation files found in uploads/history/")
            print("   Please add YYYYMMDD.xlsx files to uploads/history/ folder")
            return

        print(f"📚 Found {len(history_files)} historical quotation file(s)")
        print()

        total_added = 0
        total_updated = 0
        total_errors = 0
        files_processed = 0
        files_skipped = 0

        for file_path in history_files:
            filename = os.path.basename(file_path)
            date_str = filename.replace('.xlsx', '').replace('.xls', '')

            try:
                # Extract date from filename (YYYYMMDD format)
                date = datetime.strptime(date_str, '%Y%m%d').date()
            except ValueError:
                print(f"❌ Skipping {filename}: Invalid filename format (expected YYYYMMDD.xlsx)")
                files_skipped += 1
                continue

            print(f"📄 Processing: {filename} (date: {date})")

            try:
                # Parse quotation file
                entries = read_historical_quotation(file_path, date)

                if not entries:
                    print(f"⚠️  No valid entries found in {filename}")
                    files_skipped += 1
                    continue

                print(f"   Found {len(entries)} entries")

                # Import to database
                added_count = 0
                updated_count = 0
                error_count = 0

                for entry in entries:
                    try:
                        # Check if entry already exists
                        existing = QuotationHistory.query.filter_by(
                            date=entry['date'],
                            merchant=entry['merchant'],
                            title=entry['title']
                        ).first()

                        if existing:
                            # Update existing entry
                            existing.count = entry['count']
                            existing.price = entry['price']
                            existing.total_price = entry['total_price']
                            existing.updated_at = datetime.utcnow()
                            updated_count += 1
                        else:
                            # Insert new entry
                            qh = QuotationHistory(**entry)
                            db.session.add(qh)
                            added_count += 1

                    except Exception as e:
                        print(f"   ❌ Error importing entry: {e}")
                        error_count += 1
                        continue

                # Commit changes for this file
                db.session.commit()

                print(f"   ✅ Added: {added_count}, Updated: {updated_count}, Errors: {error_count}")
                print()

                total_added += added_count
                total_updated += updated_count
                total_errors += error_count
                files_processed += 1

            except Exception as e:
                print(f"   ❌ Error processing file: {e}")
                db.session.rollback()
                files_skipped += 1
                continue

        # Final summary
        print("=" * 60)
        print("Quotation History Initialization Complete")
        print("=" * 60)
        print(f"Files processed: {files_processed}")
        print(f"Files skipped: {files_skipped}")
        print(f"Total entries added: {total_added}")
        print(f"Total entries updated: {total_updated}")
        print(f"Total errors: {total_errors}")
        print()

        # Show total count in database
        total_count = QuotationHistory.query.count()
        print(f"📊 Total quotation history records in database: {total_count}")


if __name__ == '__main__':
    init_quotation_history()
