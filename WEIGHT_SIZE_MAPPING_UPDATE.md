# Product Weight/Size Mapping Update

## Summary

Updated the data processor to automatically populate '箱重量' (box weight) and '箱尺寸' (box size) columns from the database product mappings during Excel file processing.

## Changes Made

### 1. Updated `data_processor.py`

**Added new function:**
```python
def load_product_mappings_from_db():
    """Load product weight/size mappings from database"""
    try:
        mappings = ProductMapping.query.all()
        return {m.product_name: {'weight': m.box_weight, 'size': m.box_size} for m in mappings}
    except Exception as e:
        print(f"Warning: Could not load product mappings from database: {e}")
        return {}
```

**Added automatic population logic in `process_manufacturer_data()`:**
- Loads all product mappings from database
- Populates '箱重量' column with weight data
- Populates '箱尺寸' column with size data
- Only fills missing values (preserves existing data from Excel)
- Includes weight and size in the aggregated summary

### 2. Behavior

#### For New Columns
If '箱重量' or '箱尺寸' columns don't exist in the Excel file:
- Creates the columns automatically
- Populates them with database mappings

#### For Existing Columns
If columns already exist in the Excel file:
- Preserves existing non-null values
- Only fills null/missing values with database mappings
- Excel data takes priority over database data

#### Summary Output
The aggregated summary now includes:
- `box_weight` - First value from grouped products
- `box_size` - First value from grouped products

## Test Results

Testing with sample file (20251226-5.xlsx):
- ✅ Processed 177 unique product combinations
- ✅ 44/177 products (24%) have weight mappings
- ✅ 44/177 products (24%) have size mappings
- ✅ Weight and size columns successfully added to summary

Sample output:
```
えちえち膣バサミ: 24.8kg, 65*40*47
おなほのあほすたさん: 20.2kg, 69*42*36
丸飲み！ギャルロング: 14.4kg, 67*44*29
```

## Usage

### For End Users

1. **Manage Mappings via UI:**
   - Navigate to `/products/mappings`
   - Add/edit product weight and size mappings
   - Changes are immediately available for next report generation

2. **Generate Reports:**
   - Upload Excel files as usual
   - System automatically enriches data with weight/size from database
   - Generated reports include weight and size columns

### For Data Population

```bash
# Populate product mappings from existing Excel files
python init_product_mapping.py
```

This extracts unique products and their weight/size from all Excel files in `uploads/` folder.

## Benefits

### Before
- ❌ Weight and size data only available if in Excel file
- ❌ No centralized mapping database
- ❌ Manual data entry for each file

### After
- ✅ Automatic enrichment from database
- ✅ 196 products pre-populated from historical data
- ✅ User-editable via web interface
- ✅ Consistent data across all reports
- ✅ Excel data takes priority (if present)
- ✅ Missing data filled from database

## Data Flow

```
Excel File Upload
    ↓
Read Excel Data
    ↓
Load Product Mappings from DB
    ↓
Populate '箱重量' & '箱尺寸' columns
    (only fill missing values)
    ↓
Process & Aggregate
    ↓
Generate Report with Weight/Size
```

## Database Integration

The system uses the existing `ProductMapping` table:
- **product_name** (unique) - Product identifier
- **box_weight** (float) - Weight in kg
- **box_size** (string) - Size format: "长*宽*高" (e.g., "41*36*25")

## Error Handling

- Database connection errors fall back to empty mappings
- Warning message printed if database unavailable
- Processing continues without weight/size data
- No impact on other functionality

## Current Statistics

- **Total products in database:** 196
- **With weight data:** 44 (22%)
- **With size data:** 44 (22%)
- **Coverage in test file:** 24% of products

## Future Improvements

1. **Bulk Import**: Import weight/size from Excel batch files
2. **Auto-learning**: Automatically add new products from uploaded files
3. **Validation**: Check weight/size format before saving
4. **History**: Track changes to weight/size over time
5. **Coverage Report**: Show which products lack mappings

## Technical Notes

- Uses pandas `.apply()` with lambda for efficient mapping
- Preserves original data when available
- Aggregates using `'first'` to get one value per product group
- Compatible with existing report generation pipeline
- No breaking changes to existing functionality

## Summary

This update seamlessly integrates the database-backed product mapping system with the data processing pipeline, automatically enriching Excel data with weight and size information while preserving user control through the web interface.
