#!/usr/bin/env python3
"""Test coverage of ProductMapping after KNOWN_NAMES matching"""

from app import app
from data_processor import load_product_mappings_from_db, load_known_names_from_db
import pandas as pd
import re

with app.app_context():
    # Load test file
    test_file = 'uploads/20251226-part-1.xlsx'
    df = pd.read_excel(test_file)

    print(f'📄 Original file: {len(df)} rows, {df["品名"].nunique()} unique products')
    print()

    # Apply KNOWN_NAMES matching (same logic as data_processor)
    KNOWN_NAMES = load_known_names_from_db()
    print(f'📚 KNOWN_NAMES in database: {len(KNOWN_NAMES)}')
    pattern = '(?i)(' + '|'.join(map(re.escape, KNOWN_NAMES)) + ')'

    df['品名_original'] = df['品名']
    df['品名'] = df['品名'].str.extract(pattern, expand=True)[0].fillna(df['品名'])

    # Load ProductMapping
    product_mappings = load_product_mappings_from_db()
    db_products = set(product_mappings.keys())

    print(f'📦 ProductMapping in database: {len(db_products)} products')
    print()

    # Check coverage BEFORE matching
    excel_products_before = df['品名_original'].unique()
    matches_before = [p for p in excel_products_before if p in db_products]

    # Check coverage AFTER matching
    excel_products_after = df['品名'].unique()
    matches_after = [p for p in excel_products_after if p in db_products]

    print('=' * 70)
    print('COVERAGE COMPARISON')
    print('=' * 70)
    print()
    print(f'BEFORE KNOWN_NAMES matching:')
    print(f'  Unique products: {len(excel_products_before)}')
    print(f'  Matches: {len(matches_before)}/{len(excel_products_before)} ({len(matches_before)/len(excel_products_before)*100:.1f}%)')
    print()
    print(f'AFTER KNOWN_NAMES matching:')
    print(f'  Unique products: {len(excel_products_after)}')
    print(f'  Matches: {len(matches_after)}/{len(excel_products_after)} ({len(matches_after)/len(excel_products_after)*100:.1f}%)')
    print()
    print(f'IMPROVEMENT: {len(matches_after) - len(matches_before)} more products matched')
    print(f'             {((len(matches_after)/len(excel_products_after)) - (len(matches_before)/len(excel_products_before)))*100:.1f}% increase in coverage')
    print()

    # Show examples of transformation
    print('=' * 70)
    print('EXAMPLES OF KNOWN_NAMES MATCHING')
    print('=' * 70)
    changed = df[df['品名'] != df['品名_original']].head(15)
    for _, row in changed.iterrows():
        in_db = '✅ IN DB' if row['品名'] in db_products else '❌ NOT IN DB'
        print(f'\n{in_db}')
        print(f'  Original: {row["品名_original"]}')
        print(f'  Matched:  {row["品名"]}')
