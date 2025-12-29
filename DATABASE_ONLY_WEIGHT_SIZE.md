# Database-Only Weight/Size Implementation 仅从数据库读取重量/尺寸实现

## Summary 概述

Updated the data processor to read weight and size information **exclusively** from the ProductMapping database table. Excel files no longer provide or update weight/size data.

更新了数据处理器，**仅从** ProductMapping 数据库表读取重量和尺寸信息。Excel文件不再提供或更新重量/尺寸数据。

## Changes Made 所做更改

### 1. Removed Auto-Update from Excel 移除Excel自动更新

**Before 之前:**
```python
# Populated weight/size from database OR Excel files
if '箱重量' not in master_df.columns:
    master_df['箱重量'] = master_df['品名'].apply(get_weight)
else:
    # Fill missing values with database mappings
    master_df['箱重量'] = master_df.apply(
        lambda row: get_weight(row['品名']) if pd.isna(row['箱重量']) else row['箱重量'],
        axis=1
    )

# Update database with Excel data
update_product_mappings_from_excel(master_df)
```

**After 之后:**
```python
# Always populate weight/size ONLY from database
# Ignores any 箱重量/箱尺寸 columns in Excel files
master_df['箱重量'] = master_df['品名'].apply(get_weight)
master_df['箱尺寸'] = master_df['品名'].apply(get_size)

# No auto-update function called
```

### 2. Deprecated Auto-Update Function 弃用自动更新函数

The `update_product_mappings_from_excel()` function has been deprecated and commented out:

```python
# DEPRECATED: No longer auto-updating from Excel files
# All weight/size data now comes exclusively from ProductMapping table
# Use rebuild_product_mapping.py to update ProductMapping from source Excel files
```

### 3. Added Column Mapping 添加列映射

Added automatic column renaming for source Excel files:

```python
# Standardize column names from source Excel files
# Map '日文名字' to '品名' if it exists
if '日文名字' in df.columns and '品名' not in df.columns:
    df.rename(columns={'日文名字': '品名'}, inplace=True)
```

## Data Flow 数据流

### Old Flow 旧流程
```
Excel Upload (may have 箱重量/箱尺寸)
    ↓
Read Excel columns if available
    ↓
Fill missing values from ProductMapping
    ↓
Update ProductMapping with Excel data ← Problem!
    ↓
Generate Report
```

**Problems with old flow 旧流程的问题:**
- ❌ Two sources of truth (Excel + Database)
- ❌ Excel could overwrite database
- ❌ Inconsistent data
- ❌ Auto-updates unpredictable

### New Flow 新流程
```
Excel Upload (箱重量/箱尺寸 ignored)
    ↓
Read product names only
    ↓
Lookup weight/size from ProductMapping ONLY ← Single source!
    ↓
Generate Report
```

**Benefits of new flow 新流程的优势:**
- ✅ Single source of truth (ProductMapping database)
- ✅ Excel cannot overwrite database
- ✅ Consistent data across all reports
- ✅ Predictable behavior

## Updating ProductMapping Table 更新ProductMapping表

### Method 1: Rebuild from Source Files 方法1：从源文件重建

Use the rebuild script to update from source Excel files (those with 日文名字, 规格, 单件净重):

使用重建脚本从源Excel文件更新（包含日文名字、规格、单件净重的文件）：

```bash
source venv/bin/activate
python rebuild_product_mapping.py
```

This will:
- Clear existing ProductMapping table
- Extract data from all Excel files in `uploads/` folder
- Create 685+ product mappings
- Generate duplicate report

### Method 2: Manual Web Interface 方法2：手动网页界面

Visit the Products Manager page:

访问产品管理页面：

```
http://localhost:8000/products/mappings
```

- Add new products manually
- Edit existing products
- Delete outdated products
- Search and manage all mappings

## Single Source of Truth 单一数据源

### ProductMapping Table = Authority ProductMapping表 = 权威源

```
ProductMapping Table 产品映射表
    ├─ product_name (品名)        ← From '日文名字' in source files
    ├─ box_weight (箱重量)        ← From '单件净重(kg)' in source files
    └─ box_size (箱尺寸)          ← From '规格' in source files

↓ Used by 用于

Report Generation 报表生成
    ├─ Reads ProductMapping for each 品名
    ├─ Populates 箱重量 column
    └─ Populates 箱尺寸 column
```

### Excel Files Role Excel文件的角色

**Source Excel Files 源Excel文件** (in `uploads/`):
- Contain: 日文名字, 规格, 单件净重(kg)
- Used ONLY for rebuilding ProductMapping table
- Processed by: `rebuild_product_mapping.py`

**Report Excel Files 报表Excel文件** (uploaded via web):
- Contain: 品牌, 品名, Pcs, Price, 型番, etc.
- Do NOT contain: 箱重量, 箱尺寸
- Weight/size added from ProductMapping database

## Benefits 优势

### Data Integrity 数据完整性
- ✅ No accidental overwrites
- ✅ ProductMapping cannot be corrupted by uploads
- ✅ Controlled updates via rebuild script only
- ✅ Web interface for manual adjustments

### Consistency 一致性
- ✅ All reports use same weight/size data
- ✅ Same product always has same weight/size
- ✅ No variation between files
- ✅ Predictable results

### Maintainability 可维护性
- ✅ Clear separation: source data vs report data
- ✅ Simple data flow
- ✅ Easy to debug
- ✅ Easy to update

### Performance 性能
- ✅ No database writes during report generation
- ✅ Faster processing (read-only operations)
- ✅ No transaction overhead

## Code Changes 代码更改

### data_processor.py

**Lines 17-29:** Deprecated `update_product_mappings_from_excel()` function
```python
# DEPRECATED: No longer auto-updating from Excel files
# All weight/size data now comes exclusively from ProductMapping table
# Use rebuild_product_mapping.py to update ProductMapping from source Excel files
```

**Lines 150-153:** Added column mapping for source files
```python
# Standardize column names from source Excel files
# Map '日文名字' to '品名' if it exists
if '日文名字' in df.columns and '品名' not in df.columns:
    df.rename(columns={'日文名字': '品名'}, inplace=True)
```

**Lines 290-306:** Simplified to database-only lookup
```python
# Load product weight/size mappings from database ONLY
# Excel files should NOT contain 箱重量 or 箱尺寸 - all data comes from ProductMapping table
product_mappings = load_product_mappings_from_db()

# Always populate 箱重量 and 箱尺寸 from database, ignoring any Excel columns
master_df['箱重量'] = master_df['品名'].apply(get_weight)
master_df['箱尺寸'] = master_df['品名'].apply(get_size)
```

## Migration Notes 迁移说明

### If You Have Existing Reports 如果有现有报表

No action needed! Reports will continue to work normally.
无需操作！报表将继续正常工作。

### If You Need to Update Weight/Size 如果需要更新重量/尺寸

1. **Option 1 选项1:** Use web interface at `/products/mappings`
2. **Option 2 选项2:** Run `python rebuild_product_mapping.py` to rebuild from source files

### If Excel Files Have 箱重量/箱尺寸 如果Excel文件包含箱重量/箱尺寸

These columns will be **ignored**. The system will:
这些列将被**忽略**。系统将：

1. Read 品名 from Excel
2. Look up weight/size from ProductMapping database
3. Use database values (not Excel values)
4. Excel columns have no effect

## Testing 测试

Verified behavior:
已验证行为：

- ✅ Excel files without 箱重量/箱尺寸: Works (reads from database)
- ✅ Excel files with 箱重量/箱尺寸: Works (ignores Excel, reads from database)
- ✅ Products in database: Gets correct weight/size
- ✅ Products NOT in database: Gets null weight/size
- ✅ Web interface CRUD operations: All working
- ✅ rebuild_product_mapping.py: Working (685 products)

## Current State 当前状态

```
ProductMapping Table: 685 products
  - All have box_size (100%)
  - All have box_weight (100%)
  - Source: Rebuilt from 39 Excel files
  - Last updated: Recent rebuild

Data Flow:
  Excel → Read 品名 only
  品名 → Lookup in ProductMapping
  ProductMapping → Provide 箱重量 & 箱尺寸
  Result → Report with weight/size
```

## Summary 总结

The system now uses the ProductMapping database as the **single source of truth** for weight and size data. Excel files no longer influence this data during report generation, ensuring consistency and data integrity.

系统现在使用 ProductMapping 数据库作为重量和尺寸数据的**单一权威源**。Excel文件在报表生成期间不再影响这些数据，确保一致性和数据完整性。

**To update ProductMapping 更新ProductMapping:**
- Use `rebuild_product_mapping.py` script
- Or use web interface at `/products/mappings`

**Excel files role Excel文件的角色:**
- Provide product names and other data
- Weight/size always comes from database
- No auto-updates to database
