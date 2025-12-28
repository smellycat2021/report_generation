"""
Script to populate brand mappings from the value_mapping dictionary
in data_processor.py into the database.
"""
from app import app
from database import db, BrandMapping

# This is from data_processor.py line 154
value_mapping = {
    '072LABO': '072LABO',
    'AO': 'A-one',
    "AVS Collector's": "AVS Collector's",
    'FANTASTICBABY': 'FANTASTICBABY',
    'HP': 'Hotpowers',
    'ME': 'MagicEyes',
    'PT': 'Peach Toys',
    'RJ': 'Ride Japan',
    'TH': 'Toys Heart',
    'TMT': 'Tamatoys',
    'アリスJAPAN': '爱丽丝',
    'キテルキテル': 'Kiteru Kiteru',
    'ハトプラ': 'EXE',
    'ハトプラ(EXE)': 'EXE',
    'ハトプラ(GPRO)': 'EXE',
    'ハトプラ(HATOPLA)': 'EXE',
    'ハトプラ(PPP)': 'EXE',
}

def populate_brand_mappings():
    """
    Populate the database with brand mappings from value_mapping dictionary.
    """
    with app.app_context():
        added_count = 0
        updated_count = 0
        skipped_count = 0

        for brand_name, reference_name in value_mapping.items():
            # Check if mapping already exists
            existing = BrandMapping.query.filter_by(brand_name=brand_name).first()

            if existing:
                # Update if reference name changed
                if existing.reference_name != reference_name:
                    existing.reference_name = reference_name
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                # Add new mapping
                new_mapping = BrandMapping(
                    brand_name=brand_name,
                    reference_name=reference_name
                )
                db.session.add(new_mapping)
                added_count += 1

        db.session.commit()

        print(f"\nBrand Mapping Population Results:")
        print(f"  - Added: {added_count} new mappings")
        print(f"  - Updated: {updated_count} existing mappings")
        print(f"  - Skipped: {skipped_count} (already up-to-date)")
        print(f"\nTotal brand mappings in database: {BrandMapping.query.count()}")

if __name__ == '__main__':
    populate_brand_mappings()
