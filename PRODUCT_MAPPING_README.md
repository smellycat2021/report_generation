# Product Mapping System

This system manages the mapping of product names (品名) to their box weight (箱重量) and box size (箱尺寸).

## Features

- **Database Model**: `ProductMapping` table stores product name, box weight, and box size
- **REST API**: Full CRUD operations for managing product mappings
- **Web UI**: User-friendly interface for viewing and editing mappings
- **Auto-population**: Script to extract mappings from uploaded Excel files

## Database Schema

```sql
CREATE TABLE product_mapping (
    id INTEGER PRIMARY KEY,
    product_name VARCHAR(255) UNIQUE NOT NULL,  -- 品名
    box_weight FLOAT,                            -- 箱重量 (kg)
    box_size VARCHAR(100),                       -- 箱尺寸 (e.g., "41*36*25")
    created_at DATETIME,
    updated_at DATETIME
);
```

## API Endpoints

### GET `/api/product-mappings`
Get all product mappings with pagination and search.

**Query Parameters:**
- `search` (optional): Search by product name
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 50)

**Response:**
```json
{
  "items": [...],
  "total": 196,
  "page": 1,
  "per_page": 50,
  "pages": 4
}
```

### GET `/api/product-mappings/<id>`
Get a specific product mapping by ID.

**Response:**
```json
{
  "id": 1,
  "product_name": "360 FETISH 潮SPLASH CORONA HARD",
  "box_weight": 20.3,
  "box_size": "60*40*39",
  "created_at": "2025-12-28T14:12:39.541980",
  "updated_at": "2025-12-28T14:12:39.541985"
}
```

### POST `/api/product-mappings`
Create a new product mapping.

**Request Body:**
```json
{
  "product_name": "New Product",
  "box_weight": 12.5,
  "box_size": "41*36*25"
}
```

### PUT `/api/product-mappings/<id>`
Update an existing product mapping.

**Request Body:**
```json
{
  "product_name": "Updated Name",
  "box_weight": 13.0,
  "box_size": "42*37*26"
}
```

### DELETE `/api/product-mappings/<id>`
Delete a product mapping.

## Web Interface

Access the product mapping manager at: **http://localhost:5000/product-mappings**

Features:
- View all product mappings in a paginated table
- Search products by name
- Add new product mappings
- Edit existing mappings
- Delete mappings
- Navigation link from main page

## Initial Data Population

To extract and populate product mappings from Excel files:

```bash
source venv/bin/activate
python init_product_mapping.py
```

This script:
1. Scans all Excel files in the `uploads/` folder
2. Extracts unique products with their weight and size
3. Populates the database (updates existing, adds new)
4. Reports statistics on added/updated/skipped items

## Usage in Data Processing

The product mappings can be used in your data processing pipeline to:
- Fill in missing weight/size data for products
- Validate weight/size values against known mappings
- Generate reports with standardized product dimensions

Example integration in `data_processor.py`:

```python
from database import db, ProductMapping

def enrich_with_product_mapping(df):
    """Add weight and size from product mapping table"""
    mappings = {m.product_name: (m.box_weight, m.box_size)
                for m in ProductMapping.query.all()}

    df['箱重量'] = df['品名'].map(lambda x: mappings.get(x, (None, None))[0])
    df['箱尺寸'] = df['品名'].map(lambda x: mappings.get(x, (None, None))[1])

    return df
```

## Files Created

- `database.py` - Added `ProductMapping` model
- `app.py` - Added API endpoints and route for product mappings page
- `templates/product-mappings.html` - Web UI for managing mappings
- `init_product_mapping.py` - Script to populate database from Excel files
- `templates/index.html` - Added navigation link to product mappings

## Current Statistics

Total products in database: **196**
- Extracted from Excel files in `uploads/` folder
- Mix of products with complete and partial weight/size data
