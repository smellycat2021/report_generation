#!/usr/bin/env python3
"""
Test coverage analysis: What if we use ProductMapping product names as KNOWN_NAMES?

This script analyzes how many products from Excel files would get weight/size data
if we use all product names from ProductMapping table as additional known names for matching.
"""

from app import app
from data_processor import load_product_mappings_from_db, load_known_names_from_db
import pandas as pd
import re
import os
import glob

def analyze_coverage_with_product_mapping_as_known_names():
    """
    Analyze coverage using ProductMapping product names as KNOWN_NAMES
    """
    with app.app_context():
        # Load current data
        KNOWN_NAMES = load_known_names_from_db()
        product_mappings = load_product_mappings_from_db()

        print("=" * 80)
        print("COVERAGE ANALYSIS: Using ProductMapping as KNOWN_NAMES")
        print("=" * 80)
        print()

        print(f"📚 Current KNOWN_NAMES count: {len(KNOWN_NAMES)}")
        print(f"📦 ProductMapping products count: {len(product_mappings)}")
        print()

        # Create combined KNOWN_NAMES (current + all ProductMapping product names)
        combined_known_names = set(KNOWN_NAMES)
        product_mapping_names = set(product_mappings.keys())
        combined_known_names.update(product_mapping_names)

        print(f"🔗 Combined KNOWN_NAMES count: {len(combined_known_names)}")
        print(f"   - Original KNOWN_NAMES: {len(KNOWN_NAMES)}")
        print(f"   - ProductMapping names: {len(product_mapping_names)}")
        print(f"   - New additions: {len(product_mapping_names - set(KNOWN_NAMES))}")
        print()

        # Process all Excel files in uploads/
        excel_files = glob.glob('uploads/*.xlsx') + glob.glob('uploads/*.xls')

        if not excel_files:
            print("⚠️  No Excel files found in uploads/ folder")
            return

        print(f"📄 Found {len(excel_files)} Excel files in uploads/")
        print()

        all_results = []

        for excel_file in excel_files:
            try:
                df = pd.read_excel(excel_file)

                # Check if this is a manufacturer file (has 品名 or 日文名字)
                if '品名' not in df.columns and '日文名字' not in df.columns:
                    continue

                # Standardize column name
                if '日文名字' in df.columns and '品名' not in df.columns:
                    df.rename(columns={'日文名字': '品名'}, inplace=True)

                if '品名' not in df.columns:
                    continue

                # Get original unique products
                original_products = df['品名'].unique()
                original_products = [p for p in original_products if pd.notna(p)]

                # Scenario 1: Current KNOWN_NAMES only
                pattern_current = '(?i)(' + '|'.join(map(re.escape, KNOWN_NAMES)) + ')'
                df['品名_current'] = df['品名'].str.extract(pattern_current, expand=True)[0].fillna(df['品名'])
                matched_current = df['品名_current'].unique()
                coverage_current = sum(1 for p in matched_current if p in product_mappings) / len(matched_current) * 100

                # Scenario 2: Combined KNOWN_NAMES (current + ProductMapping)
                pattern_combined = '(?i)(' + '|'.join(map(re.escape, list(combined_known_names))) + ')'
                df['品名_combined'] = df['品名'].str.extract(pattern_combined, expand=True)[0].fillna(df['品名'])
                matched_combined = df['品名_combined'].unique()
                coverage_combined = sum(1 for p in matched_combined if p in product_mappings) / len(matched_combined) * 100

                # Count products with weight/size
                products_with_data_current = sum(1 for p in matched_current if p in product_mappings)
                products_with_data_combined = sum(1 for p in matched_combined if p in product_mappings)

                result = {
                    'file': os.path.basename(excel_file),
                    'original_count': len(original_products),
                    'current_unique': len(matched_current),
                    'current_coverage': coverage_current,
                    'current_with_data': products_with_data_current,
                    'combined_unique': len(matched_combined),
                    'combined_coverage': coverage_combined,
                    'combined_with_data': products_with_data_combined,
                    'improvement': coverage_combined - coverage_current
                }

                all_results.append(result)

            except Exception as e:
                print(f"❌ Error processing {excel_file}: {e}")
                continue

        if not all_results:
            print("⚠️  No valid manufacturer files found (files must have 品名 or 日文名字 column)")
            return

        # Print detailed results
        print("=" * 80)
        print("DETAILED FILE-BY-FILE ANALYSIS")
        print("=" * 80)
        print()

        for result in all_results:
            print(f"📄 {result['file']}")
            print(f"   Original products: {result['original_count']}")
            print()
            print(f"   Current KNOWN_NAMES (50 names):")
            print(f"      Unique after matching: {result['current_unique']}")
            print(f"      With weight/size: {result['current_with_data']}/{result['current_unique']} ({result['current_coverage']:.1f}%)")
            print()
            print(f"   Combined KNOWN_NAMES ({len(combined_known_names)} names):")
            print(f"      Unique after matching: {result['combined_unique']}")
            print(f"      With weight/size: {result['combined_with_data']}/{result['combined_unique']} ({result['combined_coverage']:.1f}%)")
            print()
            if result['improvement'] > 0:
                print(f"   ✅ Improvement: +{result['improvement']:.1f}% coverage")
            else:
                print(f"   ⚠️  No improvement")
            print()
            print("-" * 80)
            print()

        # Overall summary
        print("=" * 80)
        print("OVERALL SUMMARY")
        print("=" * 80)
        print()

        total_original = sum(r['original_count'] for r in all_results)
        total_current_unique = sum(r['current_unique'] for r in all_results)
        total_current_with_data = sum(r['current_with_data'] for r in all_results)
        total_combined_unique = sum(r['combined_unique'] for r in all_results)
        total_combined_with_data = sum(r['combined_with_data'] for r in all_results)

        avg_current_coverage = total_current_with_data / total_current_unique * 100 if total_current_unique > 0 else 0
        avg_combined_coverage = total_combined_with_data / total_combined_unique * 100 if total_combined_unique > 0 else 0

        print(f"Files analyzed: {len(all_results)}")
        print(f"Total original unique products: {total_original}")
        print()
        print(f"Current KNOWN_NAMES (50 names):")
        print(f"   Total unique after matching: {total_current_unique}")
        print(f"   Total with weight/size: {total_current_with_data}")
        print(f"   Average coverage: {avg_current_coverage:.1f}%")
        print()
        print(f"Combined KNOWN_NAMES ({len(combined_known_names)} names):")
        print(f"   Total unique after matching: {total_combined_unique}")
        print(f"   Total with weight/size: {total_combined_with_data}")
        print(f"   Average coverage: {avg_combined_coverage:.1f}%")
        print()
        print(f"📈 Overall improvement: +{avg_combined_coverage - avg_current_coverage:.1f}% coverage")
        print(f"📈 Additional products with data: +{total_combined_with_data - total_current_with_data} products")
        print()

        # Show some examples of new matches
        print("=" * 80)
        print("EXAMPLE NEW MATCHES")
        print("=" * 80)
        print()

        # Get a sample file to show examples
        sample_file = excel_files[0]
        df_sample = pd.read_excel(sample_file)

        if '日文名字' in df_sample.columns and '品名' not in df_sample.columns:
            df_sample.rename(columns={'日文名字': '品名'}, inplace=True)

        if '品名' in df_sample.columns:
            # Apply both patterns
            pattern_current = '(?i)(' + '|'.join(map(re.escape, KNOWN_NAMES)) + ')'
            pattern_combined = '(?i)(' + '|'.join(map(re.escape, list(combined_known_names))) + ')'

            df_sample['品名_current'] = df_sample['品名'].str.extract(pattern_current, expand=True)[0].fillna(df_sample['品名'])
            df_sample['品名_combined'] = df_sample['品名'].str.extract(pattern_combined, expand=True)[0].fillna(df_sample['品名'])

            # Find examples where combined matching helps
            df_sample['improved'] = (df_sample['品名_current'] != df_sample['品名_combined']) & \
                                   (df_sample['品名_combined'].isin(product_mappings.keys()))

            improved_examples = df_sample[df_sample['improved']].head(10)

            if len(improved_examples) > 0:
                print(f"Examples from {os.path.basename(sample_file)}:")
                print()
                for _, row in improved_examples.iterrows():
                    print(f"Original:         {row['品名']}")
                    print(f"Current match:    {row['品名_current']} {'✅' if row['品名_current'] in product_mappings else '❌'}")
                    print(f"Combined match:   {row['品名_combined']} {'✅' if row['品名_combined'] in product_mappings else '❌'}")
                    if row['品名_combined'] in product_mappings:
                        mapping = product_mappings[row['品名_combined']]
                        print(f"   Weight: {mapping.get('box_weight', 'N/A')} kg")
                        print(f"   Size: {mapping.get('box_size', 'N/A')}")
                    print()
            else:
                print("No improved matches found in sample file")

        print("=" * 80)
        print()

        # Recommendation
        print("💡 RECOMMENDATION:")
        print()
        if avg_combined_coverage - avg_current_coverage > 5:
            print("✅ Using ProductMapping names as KNOWN_NAMES provides significant improvement!")
            print(f"   Coverage increase: +{avg_combined_coverage - avg_current_coverage:.1f}%")
            print(f"   Additional products: +{total_combined_with_data - total_current_with_data}")
            print()
            print("Consider updating KNOWN_NAMES to include all ProductMapping product names.")
        elif avg_combined_coverage - avg_current_coverage > 0:
            print("⚠️  Using ProductMapping names as KNOWN_NAMES provides minor improvement.")
            print(f"   Coverage increase: +{avg_combined_coverage - avg_current_coverage:.1f}%")
            print(f"   Additional products: +{total_combined_with_data - total_current_with_data}")
            print()
            print("The improvement is small but may still be worth implementing.")
        else:
            print("❌ Using ProductMapping names as KNOWN_NAMES does not improve coverage.")
            print("   Current KNOWN_NAMES are sufficient.")

if __name__ == '__main__':
    analyze_coverage_with_product_mapping_as_known_names()
