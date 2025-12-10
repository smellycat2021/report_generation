# data_processor.py
import pandas as pd
import os
import numpy as np
import re

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
            
            # Apply standard column renaming using the config
            # Example: df.rename(columns=mapping_config[os.path.basename(path)], inplace=True)
            
            # Drop rows with missing critical data
            df.dropna(subset=['Maker', 'TITLE'], inplace=True)
            
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

    # find if name matches known product name
    KNOWN_NAMES = [
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
    # Escape special characters and join with '|' for OR logic
    # (\b ensures it matches whole words, but for substring matching, it's optional)
    # The (?i) makes the pattern case-insensitive
    pattern = '(?i)(' + '|'.join(map(re.escape, KNOWN_NAMES)) + ')'

    master_df['Name'] = (
        master_df['TITLE'].str.extract(pattern, expand=True)[0].fillna(master_df['TITLE'])
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
    master_df['price_range'] = pd.cut(
        master_df['Price'],
        bins=price_bins,
        labels=price_labels,
        right=True, # Intervals are (a, b] - means 500 goes into the '500_to_1000' category
        include_lowest=True # Ensures the lowest value in the data is captured
    )

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

    master_df['Maker'] = (
        master_df['Maker']
        .map(value_mapping)
        # The crucial step: fill the NaNs (unmapped values) 
        # with the corresponding values from the original column.
        .fillna(master_df['Maker'])
    )

    # Calculate key metrics for the board
    summary_df = master_df.groupby(['Maker', 'Name', 'price_range'], observed=True).agg(
        models=('品番', join_unique_strings),
        total_pieces=('Pcs', 'sum'),
        total_prices=('Total', 'sum'),
    ).reset_index()

    summary_df['Report'] = np.where(
        (summary_df['models'].isna()) | (summary_df['models'] == ''),
        '成人用品 型号：无型号',
        '成人用品 型号：' + summary_df['models'].astype(str)
    )
    
    return summary_df