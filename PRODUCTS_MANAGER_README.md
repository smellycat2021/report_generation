# Products Manager System

Complete system for managing product data, brand mappings, and known product names with database-backed configuration and user-friendly web interface.

## Overview

The Products Manager replaces hardcoded mappings in `data_processor.py` with database-backed, user-editable configurations accessible through a modern web UI.

## Features

### 1. **Product Mappings** (品名 → 箱重量 + 箱尺寸)
- Map product names to box weight and size
- **196 products** auto-populated from Excel files
- CRUD operations via web UI and REST API

### 2. **Brand Mappings** (品牌 normalization)
- Standardize brand names across manufacturers
- **17 brand mappings** migrated from `value_mapping`
- Original brand name → Reference name mapping

### 3. **Known Product Names** (Pattern matching set)
- Manage known product names for extraction
- **50 product names** migrated from `KNOWN_NAMES`
- Used in regex pattern matching

## Architecture

### Database Models

```python
# Product weight/size mappings
class ProductMapping(db.Model):
    product_name (unique)
    box_weight (float, kg)
    box_size (string, e.g., "41*36*25")

# Brand name standardization
class BrandMapping(db.Model):
    brand_name (unique)
    reference_name

# Known product names set
class KnownProductName(db.Model):
    product_name (unique)
```

### File Structure

```
/Users/na/Report/
├── database.py                       # Added 3 new models
├── data_processor.py                 # Updated to load from DB
├── app.py                            # Added 15 new API endpoints + 4 routes
├── init_product_mapping.py           # Populate product mappings
├── init_brand_mapping.py             # Populate brand mappings
├── init_known_names.py               # Populate known names
└── templates/
    ├── products-manager.html         # Landing page with cards
    ├── product-mappings.html         # Product weight/size manager
    ├── brand-mappings.html           # Brand mapping manager
    ├── known-names.html              # Known names manager
    └── index.html                    # Updated with link to Products Manager
```

## Routes & Endpoints

### Web Pages
- `GET /` - Main report generator (with link to Products Manager)
- `GET /products` - **Products Manager landing page**
- `GET /products/mappings` - Product mappings UI
- `GET /products/brands` - Brand mappings UI
- `GET /products/known-names` - Known product names UI

### REST API

#### Product Mappings
- `GET /api/product-mappings` - List all (paginated, searchable)
- `GET /api/product-mappings/<id>` - Get one
- `POST /api/product-mappings` - Create
- `PUT /api/product-mappings/<id>` - Update
- `DELETE /api/product-mappings/<id>` - Delete

#### Brand Mappings
- `GET /api/brand-mappings` - List all (paginated, searchable)
- `GET /api/brand-mappings/<id>` - Get one
- `POST /api/brand-mappings` - Create
- `PUT /api/brand-mappings/<id>` - Update
- `DELETE /api/brand-mappings/<id>` - Delete

#### Known Product Names
- `GET /api/known-product-names` - List all (paginated, searchable)
- `GET /api/known-product-names/<id>` - Get one
- `POST /api/known-product-names` - Create
- `PUT /api/known-product-names/<id>` - Update
- `DELETE /api/known-product-names/<id>` - Delete

## Data Migration

### Initial Setup

```bash
source venv/bin/activate

# Create all database tables
python -c "from app import app; from database import db; app.app_context().push(); db.create_all()"

# Populate product mappings from Excel files
python init_product_mapping.py

# Populate brand mappings from value_mapping
python init_brand_mapping.py

# Populate known names from KNOWN_NAMES
python init_known_names.py
```

### Migration Results
- ✅ Product Mappings: 196 products
- ✅ Brand Mappings: 17 mappings
- ✅ Known Names: 50 names

## Data Processor Integration

### Before (Hardcoded)
```python
KNOWN_NAMES = ['体位DX', '赤貝乳豆スクラブ', ...]  # 50+ hardcoded names
value_mapping = {'HP': 'Hotpowers', ...}  # Hardcoded dict
```

### After (Database-backed)
```python
from database import BrandMapping, KnownProductName

def load_brand_mappings_from_db():
    mappings = BrandMapping.query.all()
    return {m.brand_name: m.reference_name for m in mappings}

def load_known_names_from_db():
    names = KnownProductName.query.all()
    return [n.product_name for n in names]

# In process_manufacturer_data():
KNOWN_NAMES = load_known_names_from_db()
value_mapping = load_brand_mappings_from_db()
```

### Fallback Mechanism
If database is unavailable, functions fall back to hardcoded values with a warning message.

## Web UI Features

### Products Manager Landing Page
- Card-based navigation
- Real-time counts from API
- Links to all 3 management sections

### Management Pages (All 3)
- **Search**: Real-time filtering
- **Pagination**: 50-100 items per page
- **Add**: Modal form for creating new entries
- **Edit**: In-place editing via modal
- **Delete**: Confirmation before deletion
- **Alerts**: Success/error notifications

## Usage Examples

### Adding a New Brand Mapping
1. Navigate to `/products/brands`
2. Click "+ Add New Brand"
3. Enter:
   - Brand Name: `ハトプラ(NEW)`
   - Reference Name: `EXE`
4. Save

### Updating Product Weight/Size
1. Navigate to `/products/mappings`
2. Search for product name
3. Click "Edit" on the product
4. Update weight or size
5. Save

### Adding Known Product Name
1. Navigate to `/products/known-names`
2. Click "+ Add New Product Name"
3. Enter product name: `新商品名`
4. Save

## Benefits

### Before
- ❌ Hardcoded values in source code
- ❌ Requires code changes to update mappings
- ❌ No version control for data changes
- ❌ Manual Excel analysis to find products

### After
- ✅ Database-backed configuration
- ✅ User-editable via web UI
- ✅ No code deployment for data updates
- ✅ Auto-extraction from Excel files
- ✅ RESTful API for programmatic access
- ✅ Search and pagination built-in

## API Usage Example

### Get All Brand Mappings
```bash
curl http://localhost:8000/api/brand-mappings
```

### Create New Product Mapping
```bash
curl -X POST http://localhost:8000/api/product-mappings \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "新商品",
    "box_weight": 15.5,
    "box_size": "45*40*30"
  }'
```

### Update Brand Mapping
```bash
curl -X PUT http://localhost:8000/api/brand-mappings/5 \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "HP",
    "reference_name": "Hotpowers Updated"
  }'
```

## Statistics

Current database contents:
- **Product Mappings**: 196 entries
- **Brand Mappings**: 17 entries
- **Known Product Names**: 50 entries

## Future Enhancements

Potential improvements:
- Bulk import/export (CSV, Excel)
- History tracking (audit log)
- Multi-user permissions
- Product categorization
- Duplicate detection
- Validation rules

## Troubleshooting

### Database Connection Issues
If you see warnings about database loading:
```
Warning: Could not load brand mappings from database: <error>
```
The system will use hardcoded fallback values. Check:
1. Database file exists: `instance/app.db`
2. Flask app context is active
3. Database tables are created

### Running Migrations Again
Safe to re-run migration scripts - they will:
- Add new entries
- Update changed entries
- Skip existing identical entries

```bash
python init_brand_mapping.py
python init_known_names.py
python init_product_mapping.py
```

## Summary

The Products Manager provides a complete, production-ready system for managing product data with:
- 3 separate management interfaces
- 15 RESTful API endpoints
- Database-backed configuration
- Auto-migration from hardcoded values
- Modern, responsive UI
- Search and pagination
- Full CRUD operations

All changes are backwards-compatible with fallback mechanisms to ensure system stability.
