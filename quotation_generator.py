#!/usr/bin/env python3
"""
Quotation Generator
Generates quotation Excel files from matched purchase order data.
"""

import pandas as pd
from datetime import datetime
from config import REPORT_FOLDER
import os


def generate_quotation_sheet(matched_data, report_params=None):
    """
    Generate quotation sheet Excel file with empty first tab and data in second tab.

    Args:
        matched_data (pd.DataFrame): DataFrame with columns
                                      [merchant, title, count, price, total_price]
        report_params (dict, optional): Additional parameters for the report

    Returns:
        str: Filename of generated quotation sheet (quotation_YYYYMMDD_HHMMSS.xlsx)

    Excel Structure:
        - Sheet 1 ("Sheet1"): Empty (to match historical quotation format)
        - Sheet 2 ("Quotation"): Data with 5 columns [merchant, title, count, price, total_price]
    """
    # Generate timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'quotation_{timestamp}.xlsx'
    filepath = os.path.join(REPORT_FOLDER, filename)

    # Create Excel writer
    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        # Sheet 1: Empty sheet (to match historical format)
        empty_df = pd.DataFrame()
        empty_df.to_excel(writer, sheet_name='Sheet1', index=False, header=False)

        # Sheet 2: Quotation data
        # Reorder columns to ensure correct order
        output_df = matched_data[['merchant', 'title', 'count', 'price', 'total_price']].copy()

        # Rename columns to Chinese/English bilingual
        output_df.columns = [
            '商家 Merchant',
            '品名 Title',
            '数量 Count',
            '单价 Price',
            '总价 Total Price'
        ]

        # Write data to second sheet
        output_df.to_excel(writer, sheet_name='Quotation', index=False)

        # Get workbook and worksheet objects for formatting
        workbook = writer.book
        worksheet = writer.sheets['Quotation']

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#667eea',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right'
        })

        # Format header row
        for col_num, value in enumerate(output_df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Set column widths
        worksheet.set_column('A:A', 20)  # Merchant
        worksheet.set_column('B:B', 40)  # Title
        worksheet.set_column('C:C', 12)  # Count
        worksheet.set_column('D:D', 12)  # Price
        worksheet.set_column('E:E', 15)  # Total Price

        # Format numeric columns (count, price, total_price)
        # Rows start from 1 (0 is header)
        for row_num in range(1, len(output_df) + 1):
            worksheet.write_number(row_num, 2, output_df.iloc[row_num - 1]['数量 Count'], number_format)

            # Handle null prices
            price_val = output_df.iloc[row_num - 1]['单价 Price']
            if pd.notna(price_val):
                worksheet.write_number(row_num, 3, price_val, number_format)
            else:
                worksheet.write_string(row_num, 3, '', number_format)

            total_price_val = output_df.iloc[row_num - 1]['总价 Total Price']
            if pd.notna(total_price_val):
                worksheet.write_number(row_num, 4, total_price_val, number_format)
            else:
                worksheet.write_string(row_num, 4, '', number_format)

    print(f"✅ Generated quotation sheet: {filename}")
    return filename
