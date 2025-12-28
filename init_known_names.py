"""
Script to populate known product names from the KNOWN_NAMES list
in data_processor.py into the database.
"""
from app import app
from database import db, KnownProductName

# This is from data_processor.py line 59
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

def populate_known_names():
    """
    Populate the database with known product names from KNOWN_NAMES list.
    """
    with app.app_context():
        added_count = 0
        skipped_count = 0

        for product_name in KNOWN_NAMES:
            # Check if name already exists
            existing = KnownProductName.query.filter_by(product_name=product_name).first()

            if existing:
                skipped_count += 1
            else:
                # Add new known name
                new_name = KnownProductName(product_name=product_name)
                db.session.add(new_name)
                added_count += 1

        db.session.commit()

        print(f"\nKnown Product Names Population Results:")
        print(f"  - Added: {added_count} new names")
        print(f"  - Skipped: {skipped_count} (already exist)")
        print(f"\nTotal known product names in database: {KnownProductName.query.count()}")

if __name__ == '__main__':
    populate_known_names()
