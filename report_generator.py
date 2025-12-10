# report_generator.py
import pandas as pd
import os
import config

def generate_summary_report(summary_data: pd.DataFrame, report_params):
    """
    Formats the aggregated data into a professional Excel file with structure.
    """
    report_filename = f"board_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    output_path = os.path.join(config.REPORT_FOLDER, report_filename)
    
    # Use Pandas ExcelWriter to write to different sheets
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        
        # 1. Write the main summary table to the first sheet
        summary_data.to_excel(writer, sheet_name='Board Summary KPIs', index=False)
        
        # 2. Add high-level commentary or charts (requires XlsxWriter manipulation)
        # workbook = writer.book
        # worksheet = writer.sheets['Board Summary KPIs']
        # worksheet.write('A1', 'Product Performance Overview - Q4 2025')
        
        # 3. Add raw aggregated data to a separate sheet for drill-down
        # aggregated_data.to_excel(writer, sheet_name='Raw Aggregated Data', index=False)
        
    return report_filename