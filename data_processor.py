# data_processor.py
import pandas as pd
import os
import numpy as np
import re
import random
from database import BrandMapping, KnownProductName, ProductMapping

def load_product_mappings_from_db():
    """Load product weight/size mappings from database"""
    try:
        mappings = ProductMapping.query.all()
        return {m.product_name: {'weight': m.box_weight, 'size': m.box_size} for m in mappings}
    except Exception as e:
        print(f"Warning: Could not load product mappings from database: {e}")
        return {}

# DEPRECATED: No longer auto-updating from Excel files
# All weight/size data now comes exclusively from ProductMapping table
# Use rebuild_product_mapping.py to update ProductMapping from source Excel files
#
# def update_product_mappings_from_excel(df):
#     """
#     Update product mappings in database with weight/size info from Excel.
#     Only updates existing products or creates new ones if weight/size data is available.
#
#     Args:
#         df: DataFrame with columns '品名', '单件净重(kg)', '规格'
#     """
#     ...

def load_brand_mappings_from_db():
    """Load brand mappings from database"""
    try:
        mappings = BrandMapping.query.all()
        return {m.brand_name: m.reference_name for m in mappings}
    except Exception as e:
        print(f"Warning: Could not load brand mappings from database: {e}")
        # Fallback to hardcoded values if database is not available
        return {
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

def load_known_names_from_db():
    """Load known product names from database"""
    try:
        names = KnownProductName.query.all()
        return [n.product_name for n in names]
    except Exception as e:
        print(f"Warning: Could not load known names from database: {e}")
        # Fallback to hardcoded values if database is not available
        return [
            '体位DX',
            '赤貝乳豆スクラブ',
            'オナホ屋さんのだ液汁',
            '胡夢',
            '有坂深雪',
            'ポンコツガーディアンユニバース ユニコーンプレミアム肉厚ファビュラス',
            '幼馴染',
            'PUNIVIRGIN[ぷにばーじん]1000 ふわとろ',
            'Chu！［チュッ！］',
            'JAPANESE REAL HOLE',
            'ぷにあなSPDX ',
            'ぷにあなミラクル爆乳DX',
            '網',
            'けもろーしょん',
            '対魔忍',
            'ZARA GYUGYU',
            'すじまん くぱぁ ココロ',
            '極彩ウテルス ',
            'オナシー',
            'ろりんこ創世記ナマイキHARD',
            '疑似ちつ ツブびら淫スパイラル　すけすけ',
            '激フェラ',
            'まる剥がしリアル 八乃つばさ',
            'フェラ お口でちゅくします',
            '名器覚醒',
            '素人リアル',
            '名器の証明',
            '地雷系女子パンキーメッシュ',
            'ポロンコロン',
            '欲情',
            '処女くぱぁ',
            'おなつゆ(onatsuyu)370ml',
            "あほすたさん印の母乳ローション(Fake mother's milk Lubricant)",
            '現役JD',
            '匂い',
            'プルルンおっぱいニプルファック',
            '千鶴',
            '制服美少女',
            '先輩',
            '爆乳',
            '三芳の愛液',
            '360 FETISH 潮SPLASH',
            'チクニー＆チクパコ',
            'ONA砲',
            'オナホルダー',
            'AVミニ名器',
            '真実の口',
            'あこがれの美少女ブルマ',
            '名器創生',
            '素人リアル',
            '日本のローション',
        ]

def join_unique_strings(series):
    """
    Cleans the series, finds unique non-missing values, and joins them into a single string.
    """
    # 1. Drop NaN values
    series_no_nan = series.dropna()
    
    # 2. Convert all values to strings (critical for concatenation)
    series_str = series_no_nan.astype(str)
    
    # 3. Get only unique values (to avoid repetition)
    unique_values = series_str.unique()
    
    # 4. Join them with a delimiter (e.g., comma and space)
    return ', '.join(unique_values)

def process_manufacturer_data(file_paths, mapping_config):
    """
    Reads multiple manufacturer files, cleans them, and aggregates data.
    """
    all_data = []
    
    for path in file_paths:
        try:
            # 1. Excel Parsing: Read the file into a Pandas DataFrame
            df = pd.read_excel(path)

            # 2. Data Cleaning & Transformation:

            # Standardize column names from source Excel files
            # Map '日文名字' to '品名' if it exists
            if '日文名字' in df.columns and '品名' not in df.columns:
                df.rename(columns={'日文名字': '品名'}, inplace=True)

            # Drop rows with missing critical data
            df.dropna(subset=['品牌', '品名'], inplace=True)
            
            # Ensure data types are correct
            df['Pcs'] = pd.to_numeric(df['Pcs'], errors='coerce')
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
            
            all_data.append(df)
            
        except Exception as e:
            print(f"Error processing {path}: {e}")
            # Log the error and move to the next file

    # 3. Aggregation: Combine all manufacturer data
    if not all_data:
        return pd.DataFrame() # Return empty if no data
    
    master_df = pd.concat(all_data, ignore_index=True)

    # Load known product names from database
    KNOWN_NAMES = load_known_names_from_db()

    # Add all ProductMapping product names to KNOWN_NAMES for better matching coverage
    # This improves coverage from ~34% to ~59% by matching product name variants
    product_mappings = load_product_mappings_from_db()
    KNOWN_NAMES = list(set(KNOWN_NAMES) | set(product_mappings.keys()))
    print(f'📚 Combined KNOWN_NAMES: {len(KNOWN_NAMES)} names (50 original + {len(product_mappings)} from ProductMapping)')

    # Escape special characters and join with '|' for OR logic
    # (\b ensures it matches whole words, but for substring matching, it's optional)
    # The (?i) makes the pattern case-insensitive
    pattern = '(?i)(' + '|'.join(map(re.escape, KNOWN_NAMES)) + ')'

    master_df['品名'] = (
        master_df['品名'].str.extract(pattern, expand=True)[0].fillna(master_df['品名'])
    )

    # 1. Define the numerical thresholds (bins)
    # Note: The first bin must be lower than your minimum price, and the last must be higher than your maximum price.
    # Use -np.inf and np.inf to catch all possible values.
    price_bins = [
        -np.inf, # Lowest possible number
        500,     # Upper bound for the first category
        1000,    # Upper bound for the second category
        2500,    # Upper bound for the third category
        5000,    # Upper bound for the 4th category
        10000,    # Upper bound for the 5th category
        20000,    # Upper bound for the 6th category
        30000,    # Upper bound for the 7th category
        np.inf   # Highest possible number
    ]
    # 2. Define the corresponding labels (must have one less label than bins)
    price_labels = [
        'less_than_500', 
        '500_to_1000', 
        '1000_to_2500', 
        '2500_to_5000',
        '5000_to_10000', 
        '10000_to_20000', 
        '20000_to_30000', 
        'over_30000'
    ]
    master_df['价格区间'] = pd.cut(
        master_df['Price'],
        bins=price_bins,
        labels=price_labels,
        right=True, # Intervals are (a, b] - means 500 goes into the '500_to_1000' category
        include_lowest=True # Ensures the lowest value in the data is captured
    )

    # Load brand mappings from database
    value_mapping = load_brand_mappings_from_db()

    master_df['品牌'] = (
        master_df['品牌']
        .map(value_mapping)
        # The crucial step: fill the NaNs (unmapped values)
        # with the corresponding values from the original column.
        .fillna(master_df['品牌'])
    )

    # Load product weight/size mappings from database ONLY
    # Excel files should NOT contain 单件净重(kg) or 规格 - all data comes from ProductMapping table
    product_mappings = load_product_mappings_from_db()

    # Create mapping functions
    def get_weight(product_name):
        mapping = product_mappings.get(product_name)
        return mapping['weight'] if mapping and mapping['weight'] is not None else None

    def get_size(product_name):
        mapping = product_mappings.get(product_name)
        return mapping['size'] if mapping and mapping['size'] is not None else None

    # Always populate 单件净重(kg) and 规格 from database, ignoring any Excel columns
    # This ensures we ONLY use data from ProductMapping table
    master_df['单件净重(kg)'] = master_df['品名'].apply(get_weight)
    master_df['规格'] = master_df['品名'].apply(get_size)

    # Calculate 净重 (net weight) = 单件净重(kg) * Pcs
    master_df['净重'] = master_df['单件净重(kg)'] * master_df['Pcs']

    # Calculate key metrics for the board
    # Use lambda with first valid (non-null) value for weight and size
    summary_df = master_df.groupby(['品牌', '品名', '价格区间', '分類','産地'], observed=True).agg(
        型号=('型番', join_unique_strings),
        数量=('Pcs', 'sum'),
        总价格=('Total', 'sum'),
    ).reset_index()

    # Add weight and size columns separately to use Chinese column names with parentheses
    summary_df['单件净重(kg)'] = master_df.groupby(['品牌', '品名', '价格区间', '分類','産地'], observed=True)['单件净重(kg)'].apply(
        lambda x: x.dropna().iloc[0] if len(x.dropna()) > 0 else None
    ).values

    summary_df['规格'] = master_df.groupby(['品牌', '品名', '价格区间', '分類','産地'], observed=True)['规格'].apply(
        lambda x: x.dropna().iloc[0] if len(x.dropna()) > 0 else None
    ).values

    summary_df['净重'] = master_df.groupby(['品牌', '品名', '价格区间', '分類','産地'], observed=True)['净重'].sum().values

    # Replace 净重 with None if value is 0 (means no weight data available)
    summary_df['净重'] = summary_df['净重'].apply(lambda x: None if x == 0 else x)

    summary_df['毛重'] = summary_df['净重'] * random.uniform(1.08, 1.12)

    # Build 报关 column with model information
    summary_df['报关'] = np.where(
        (summary_df['型号'].isna()) | (summary_df['型号'] == ''),
        '型号：无型号',
        '型号：' + summary_df['型号'].astype(str)
    )

    # Add prefix for ADULT TOY category
    adult_toy_prefix = '成人用品 成人解决生理需求用|热塑性弹性体TPE制 '
    summary_df['报关'] = np.where(
        (summary_df['分類'] == 'ADULT TOY') | (summary_df['分類'] == 'ELECTRIC ADULT TOY') | (summary_df['分類'] == 'CLOTHING'),
        adult_toy_prefix + summary_df['报关'],
        summary_df['报关']
    )

    # add prefix for lotion category
    lotion_prefix = '润滑液人体润滑用|水90%，甘油5%，聚丙烯酸钠5%|不含从石油或沥青提取矿物油类 '
    summary_df['报关'] = np.where(
        summary_df['分類'] == 'LOTION',
        lotion_prefix + summary_df['报关'],
        summary_df['报关']
    )

    return summary_df