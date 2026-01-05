#!/usr/bin/env python3
"""
Quotation Processor
Handles parsing of historical quotation files and purchase orders,
and matching prices for quotation generation.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from database import db, QuotationHistory


def read_historical_quotation(file_path, date):
    """
    Parse historical quotation Excel file.

    Args:
        file_path (str): Path to YYYYMMDD.xlsx file
        date (datetime.date): Date object extracted from filename

    Returns:
        list: List of dicts with quotation entries
              [{"date": date, "merchant": "...", "title": "...",
                "count": 10, "price": 100, "total_price": 1000}, ...]

    Logic:
        1. Open Excel file with pd.ExcelFile()
        2. Get all sheet names
        3. Skip first sheet (index 0, should be empty)
        4. For each remaining sheet:
           - Read with header=None (no header row)
           - Extract columns: 0=merchant, 3=title, 4=count, 5=price, 6=total_price
           - Drop rows where merchant, title, count, or price is null
           - Calculate total_price = count × price if total_price is null
           - Append to results list
        5. Return list of dicts with date attached
    """
    results = []

    try:
        # Open Excel file
        with pd.ExcelFile(file_path) as xls:
            sheet_names = xls.sheet_names

            # Validate: must have at least 2 sheets (first empty, second with data)
            if len(sheet_names) < 2:
                print(f"⚠️  Warning: {file_path} has only {len(sheet_names)} sheet(s). Expected at least 2.")
                return results

            # Skip first sheet (index 0), process remaining sheets
            for sheet_idx, sheet_name in enumerate(sheet_names[1:], start=1):
                try:
                    # Read sheet without header
                    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

                    # Check if sheet has enough columns (need at least 7: indices 0-6)
                    if df.shape[1] < 7:
                        print(f"⚠️  Warning: Sheet '{sheet_name}' has only {df.shape[1]} columns. Skipping.")
                        continue

                    # Extract relevant columns
                    # Column 0 = merchant, 3 = title, 4 = count, 5 = price, 6 = total_price
                    df_extracted = df.iloc[:, [0, 3, 4, 5, 6]].copy()
                    df_extracted.columns = ['merchant', 'title', 'count', 'price', 'total_price']

                    # Convert numeric columns
                    df_extracted['count'] = pd.to_numeric(df_extracted['count'], errors='coerce')
                    df_extracted['price'] = pd.to_numeric(df_extracted['price'], errors='coerce')
                    df_extracted['total_price'] = pd.to_numeric(df_extracted['total_price'], errors='coerce')

                    # Drop rows where merchant, title, count, or price is null
                    df_extracted = df_extracted.dropna(subset=['merchant', 'title', 'count', 'price'])

                    # Calculate total_price if null
                    df_extracted['total_price'] = df_extracted.apply(
                        lambda row: row['count'] * row['price'] if pd.isna(row['total_price']) else row['total_price'],
                        axis=1
                    )

                    # Convert to list of dicts
                    for _, row in df_extracted.iterrows():
                        results.append({
                            'date': date,
                            'merchant': str(row['merchant']).strip(),
                            'title': str(row['title']).strip(),
                            'count': float(row['count']),
                            'price': float(row['price']),
                            'total_price': float(row['total_price'])
                        })

                except Exception as e:
                    print(f"❌ Error processing sheet '{sheet_name}' in {file_path}: {e}")
                    continue

    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return results

    return results


def process_purchase_order(file_path):
    """
    Parse purchase order Excel file (first tab only).

    Args:
        file_path (str): Path to purchase order XLSX file

    Returns:
        pd.DataFrame: DataFrame with columns [merchant, title, count]

    Logic:
        1. Read first tab only (sheet_name=0)
        2. Read with header=None (no header row)
        3. Extract columns: 0=merchant, 3=title, 4=count
        4. Drop rows where merchant, title, or count is null
        5. Return DataFrame
    """
    try:
        # Read first sheet only
        df = pd.read_excel(file_path, sheet_name=0, header=None)

        # Check if sheet has enough columns (need at least 5: indices 0-4)
        if df.shape[1] < 5:
            raise ValueError(f"Purchase order file has only {df.shape[1]} columns. Expected at least 5.")

        # Extract relevant columns
        # Column 0 = merchant, 3 = title, 4 = count
        df_extracted = df.iloc[:, [0, 3, 4]].copy()
        df_extracted.columns = ['merchant', 'title', 'count']

        # Convert count to numeric
        df_extracted['count'] = pd.to_numeric(df_extracted['count'], errors='coerce')

        # Drop rows with null values in critical fields
        df_extracted = df_extracted.dropna(subset=['merchant', 'title', 'count'])

        # Clean string fields
        df_extracted['merchant'] = df_extracted['merchant'].astype(str).str.strip()
        df_extracted['title'] = df_extracted['title'].astype(str).str.strip()

        print(f"✅ Parsed purchase order: {len(df_extracted)} items")
        return df_extracted

    except Exception as e:
        print(f"❌ Error processing purchase order {file_path}: {e}")
        raise


def match_prices(purchase_df):
    """
    Match purchase order items against quotation history.

    Args:
        purchase_df (pd.DataFrame): DataFrame with columns [merchant, title, count]

    Returns:
        tuple: (matched_df, match_stats)
            - matched_df: DataFrame with [merchant, title, count, price, total_price]
            - match_stats: dict with matching statistics

    Logic:
        1. For each row in purchase_df:
           a. Query QuotationHistory for matching merchant + title
           b. Order by date DESC (most recent first)
           c. Get first result (latest price)
           d. If found: set price, calculate total_price = count × price
           e. If not found: set price = None, total_price = None
        2. Return enhanced DataFrame with price/total_price columns
        3. Calculate match statistics
    """
    # Add price and total_price columns
    purchase_df['price'] = None
    purchase_df['total_price'] = None

    matched_count = 0
    unmatched_count = 0

    # Iterate through each purchase item
    for idx, row in purchase_df.iterrows():
        merchant = row['merchant']
        title = row['title']
        count = row['count']

        # Query database for matching merchant + title, ordered by most recent date
        quotation = QuotationHistory.query.filter_by(
            merchant=merchant,
            title=title
        ).order_by(QuotationHistory.date.desc()).first()

        if quotation:
            # Match found - use price from quotation history
            purchase_df.at[idx, 'price'] = quotation.price
            purchase_df.at[idx, 'total_price'] = count * quotation.price
            matched_count += 1
        else:
            # No match found - leave price and total_price as None
            unmatched_count += 1

    # Calculate match statistics
    total_items = len(purchase_df)
    match_rate = (matched_count / total_items * 100) if total_items > 0 else 0

    match_stats = {
        'total_items': total_items,
        'matched_items': matched_count,
        'unmatched_items': unmatched_count,
        'match_rate': round(match_rate, 1)
    }

    print(f"📊 Match Statistics:")
    print(f"   Total items: {total_items}")
    print(f"   Matched: {matched_count} ({match_rate:.1f}%)")
    print(f"   Unmatched: {unmatched_count}")

    return purchase_df, match_stats


def import_historical_quotation_to_db(file_path, date):
    """
    Import historical quotation file into database.

    Args:
        file_path (str): Path to YYYYMMDD.xlsx file
        date (datetime.date): Date object extracted from filename

    Returns:
        dict: Import summary with counts {added, updated, skipped, errors}
    """
    entries = read_historical_quotation(file_path, date)

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
                # Update existing entry (allows re-importing corrected data)
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
            print(f"❌ Error importing entry: {entry} - {e}")
            error_count += 1
            continue

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"❌ Database commit failed: {e}")
        raise

    return {
        'added': added_count,
        'updated': updated_count,
        'errors': error_count,
        'total_processed': added_count + updated_count
    }
