# Render Deployment Guide 部署指南

## PostgreSQL Migration - Production Ready 生产环境PostgreSQL迁移

This application now supports **PostgreSQL for production** and **SQLite for local development**. All database changes are **persistent** when deployed to Render.

本应用现在支持**生产环境使用PostgreSQL**和**本地开发使用SQLite**。部署到Render后，所有数据库更改都是**持久化的**。

---

## 📋 Prerequisites 前提条件

1. **Render Account** - Sign up at [render.com](https://render.com)
2. **GitHub Repository** - Code pushed to GitHub
3. **Excel Source Files** _(optional)_ - For rebuilding product mappings

---

## 🚀 Deployment Steps 部署步骤

### Step 1: Create PostgreSQL Database 创建PostgreSQL数据库

1. **Log in to Render Dashboard**
   - Go to [dashboard.render.com](https://dashboard.render.com)

2. **Create New PostgreSQL Database**
   - Click **"New +"** → **"PostgreSQL"**
   - Settings:
     - **Name**: `report-database` (or any name you prefer)
     - **Database**: `report_db`
     - **User**: `report_user`
     - **Region**: Choose closest to your users
     - **Plan**: **Free** (sufficient for most use cases)
   - Click **"Create Database"**

3. **Copy Database URL**
   - After creation, go to database dashboard
   - Find **"Internal Database URL"** (NOT External)
   - Copy the full URL (format: `postgres://user:password@host/database`)
   - **Keep this URL safe!** You'll need it in Step 2

---

### Step 2: Create Web Service 创建Web服务

1. **Create New Web Service**
   - Click **"New +"** → **"Web Service"**
   - Connect your GitHub repository

2. **Configure Build Settings 构建设置**
   ```
   Name: report-generator
   Region: [Same as database]
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   Plan: Free
   ```

3. **Add Environment Variables 添加环境变量**
   - Click **"Environment"** tab
   - Add the following variable:

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | _Paste the Internal Database URL from Step 1_ |

   **Example**:
   ```
   DATABASE_URL=postgres://report_user:ABC123xyz@dpg-xxxxx.oregon-postgres.render.com/report_db
   ```

4. **Deploy!**
   - Click **"Create Web Service"**
   - Wait for deployment to complete (~3-5 minutes)

---

### Step 3: Initialize Database 初始化数据库

After first deployment, the database will be empty. You have two options:

首次部署后，数据库将为空。您有两个选项：

#### Option A: Auto-Initialize (Recommended) 自动初始化（推荐）

The app will automatically initialize empty databases on startup, but you need to manually run the script once:

应用会在启动时自动初始化空数据库，但您需要手动运行一次脚本：

1. **Via Render Shell**
   - Go to your web service dashboard
   - Click **"Shell"** tab (top right)
   - Run:
     ```bash
     python init_on_startup.py
     ```

2. **What it does**:
   - Initializes 17 brand mappings
   - Initializes 50 known product names
   - Rebuilds 685 product mappings (if Excel files exist in uploads/)

#### Option B: Manual Web Interface 手动网页界面

After deployment completes:

1. Visit your Render URL: `https://your-app-name.onrender.com`
2. Go to **Products Manager** pages:
   - `/products/brands` - Add brand mappings
   - `/products/known-names` - Add known product names
   - `/products/mappings` - Add product mappings

---

## ✅ Verification 验证

### Check Database Connection 检查数据库连接

Visit your app URL and check:
```
https://your-app-name.onrender.com/api/products
```

Should return JSON with product mappings (or empty array if not initialized).

应返回包含产品映射的JSON（如果未初始化则为空数组）。

### Check Tables Populated 检查表是否填充

Via Render Shell:
```bash
python -c "
from app import app
from database import ProductMapping, BrandMapping, KnownProductName

with app.app_context():
    print(f'Products: {ProductMapping.query.count()}')
    print(f'Brands: {BrandMapping.query.count()}')
    print(f'Known Names: {KnownProductName.query.count()}')
"
```

Expected output:
```
Products: 685
Brands: 17
Known Names: 50
```

---

## 🔄 How It Works 工作原理

### Development (Local) 开发环境（本地）

```python
# No DATABASE_URL environment variable
# Uses SQLite: sqlite:///app.db
# Database file: /Users/na/Report/app.db
```

### Production (Render) 生产环境（Render）

```python
# DATABASE_URL environment variable set
# Uses PostgreSQL from Render
# Database: Persistent PostgreSQL instance
```

### Configuration Logic 配置逻辑

In [config.py](config.py):
```python
# Use PostgreSQL if DATABASE_URL exists (production)
# Otherwise use SQLite (development)
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'

# Fix Render's postgres:// → postgresql:// format
if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
```

---

## 🗂️ Data Persistence 数据持久化

### ✅ What is Persistent 什么会持久化

- **PostgreSQL Database** - All data in ProductMapping, BrandMapping, KnownProductName tables
- **User edits via web interface** - Immediately saved to PostgreSQL
- **Uploads processed** - Product mappings auto-updated in database

### ❌ What is NOT Persistent 什么不会持久化

- **Files in `uploads/` folder** - Lost on container restart (use database instead)
- **Files in `reports/` folder** - Generated reports are ephemeral
- **Logs** - Not persisted

**Solution**: All critical data is in PostgreSQL, which IS persistent!

**解决方案**：所有关键数据都在PostgreSQL中，这是持久化的！

---

## 🔧 Updating Product Data 更新产品数据

### After Deployment 部署后

You have three ways to update product data:

#### 1. **Web Interface** (Easiest) 网页界面（最简单）
```
https://your-app-name.onrender.com/products/mappings
```
- Click "Add Product" to add new products
- Edit existing products inline
- Changes saved immediately to PostgreSQL

#### 2. **Via Render Shell** (For bulk updates) 通过Shell（批量更新）
```bash
# SSH into your Render instance
# Upload Excel files, then run:
python rebuild_product_mapping.py
```

#### 3. **Re-deploy with Data** (For fresh rebuild) 重新部署（完全重建）
```bash
# Local: Rebuild from source files
python rebuild_product_mapping.py

# Commit database changes (if using SQLite locally)
git add .
git commit -m "Update product mappings"
git push

# Render will auto-deploy
```

---

## 🐛 Troubleshooting 故障排查

### Issue 1: Database Connection Error 数据库连接错误

**Error**: `could not connect to server`

**Solution**:
1. Check `DATABASE_URL` environment variable is set correctly
2. Ensure you're using **Internal Database URL** (not External)
3. Database and web service should be in **same region**

### Issue 2: Empty Database After Deployment 部署后数据库为空

**Solution**:
```bash
# Via Render Shell:
python init_on_startup.py
```

This will populate all three tables with default data.

### Issue 3: Changes Not Persisting 更改未持久化

**Check**:
1. Are you using PostgreSQL? (Check environment variable)
2. Is `DATABASE_URL` pointing to the correct database?
3. Run this to verify:
   ```bash
   echo $DATABASE_URL
   ```

### Issue 4: Old SQLite Data Not Migrated 旧SQLite数据未迁移

**Solution**:

If you have important data in local SQLite (`app.db`), you need to export and re-import:

如果本地SQLite (`app.db`) 中有重要数据，需要导出并重新导入：

```bash
# Local: Export data to Excel/CSV
python -c "
from app import app
from database import ProductMapping
import pandas as pd

with app.app_context():
    products = ProductMapping.query.all()
    data = [{
        'product_name': p.product_name,
        'box_weight': p.box_weight,
        'box_size': p.box_size
    } for p in products]
    df = pd.DataFrame(data)
    df.to_excel('product_export.xlsx', index=False)
"

# Then manually import via web interface or rebuild script
```

---

## 📊 Database Schema 数据库架构

### Tables 表

1. **ProductMapping** 产品映射
   - `product_name` (String) - Product name 产品名称
   - `box_weight` (Float) - Box weight in kg 箱重量（千克）
   - `box_size` (String) - Box size/specifications 箱尺寸/规格

2. **BrandMapping** 品牌映射
   - `brand_code` (String) - Short brand code 品牌代码
   - `brand_name` (String) - Full brand name 完整品牌名称

3. **KnownProductName** 已知产品名称
   - `name` (String) - Known product name for pattern matching 用于模式匹配的已知产品名称

---

## 🔐 Security Notes 安全注意事项

1. **Never commit DATABASE_URL to git** - Always use environment variables

   永远不要将DATABASE_URL提交到git - 始终使用环境变量

2. **Keep database credentials secure** - Don't share Internal Database URL

   保护数据库凭据安全 - 不要分享内部数据库URL

3. **Use Internal URL for web service** - External URL is for external connections only

   Web服务使用内部URL - 外部URL仅用于外部连接

---

## 📈 Monitoring 监控

### View Logs 查看日志

Render Dashboard → Your Web Service → **Logs** tab

### Database Metrics 数据库指标

Render Dashboard → Your PostgreSQL Database → **Metrics** tab

Shows:
- Connection count
- CPU usage
- Memory usage
- Storage used

---

## 💰 Cost 费用

### Free Tier Limits 免费套餐限制

**PostgreSQL Database**:
- Storage: 1 GB
- RAM: 256 MB
- **Persists for 90 days** (then deleted if not upgraded)

**Web Service**:
- 750 hours/month
- Spins down after 15 minutes of inactivity
- Starts up automatically on request

### Upgrade Options 升级选项

If you need more:
- **Starter Database**: $7/month (10 GB storage, always on)
- **Starter Web Service**: $7/month (always on, no spin down)

---

## ✨ Summary 总结

### Before (SQLite) 之前（SQLite）
- ❌ Data lost on every deployment
- ❌ Ephemeral filesystem
- ❌ Not production-ready

### After (PostgreSQL) 之后（PostgreSQL）
- ✅ Data persists across deployments
- ✅ Production-ready
- ✅ Free tier available
- ✅ Automatic backups
- ✅ Better performance

---

## 📞 Support 支持

If you encounter issues:

1. Check Render logs: Dashboard → Logs
2. Verify DATABASE_URL is set correctly
3. Run `python init_on_startup.py` to initialize database
4. Check database metrics for connection issues

遇到问题时：

1. 检查Render日志：Dashboard → Logs
2. 验证DATABASE_URL设置正确
3. 运行 `python init_on_startup.py` 初始化数据库
4. 检查数据库指标以排查连接问题

---

## 🎉 You're Done! 完成！

Your application is now deployed with persistent PostgreSQL database. All data changes will survive deployments and restarts.

您的应用现已使用持久化PostgreSQL数据库部署。所有数据更改都将在部署和重启后保留。

**Next Steps**:
1. Initialize database via Render Shell: `python init_on_startup.py`
2. Visit your app: `https://your-app-name.onrender.com`
3. Start managing products via web interface!

**下一步**：
1. 通过Render Shell初始化数据库：`python init_on_startup.py`
2. 访问您的应用：`https://your-app-name.onrender.com`
3. 开始通过网页界面管理产品！
