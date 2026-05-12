# Web Crawler Project

A web crawler built with Scrapy and MySQL, capable of crawling multiple websites simultaneously.

---

## Project Structure

```
crawler_project/
├── config.py          ← Database & Scrapy settings
├── database.py        ← MySQL connection & data saving
├── core.py            ← Main Scrapy engine (do not modify)
├── main.py            ← Run all crawlers
└── sites/
    ├── __init__.py
    └── sites.py       ← Configure websites to crawl here
```

---

## Prerequisites

- Windows 10/11
- Python 3.x
- VS Code

---

## Step 1 — Install MySQL

### 1.1 Download MySQL Installer

Go to: https://dev.mysql.com/downloads/installer/

Download the **larger file** (~565MB): `mysql-installer-community-8.0.46.0.msi`

Click **Download** → Click **"No thanks, just start my download"**

### 1.2 Run the Installer

Open the downloaded file → Click **Yes** when prompted.

In the installer screen:
- Click **Add...**
- Expand **MySQL Servers → MySQL Server → MySQL Server 8.0**
- Select **MySQL Server 8.0.46 - X64**
- Click the **→** arrow to move it to the right panel
- Click **Next → Execute**

### 1.3 Configure MySQL Server

When the configuration screen appears:

**Type and Networking screen:**
- Keep all defaults → Click **Next**

**Authentication Method screen:**
- Select **"Use Strong Password Encryption"** → Click **Next**

**Accounts and Roles screen:**
- Enter a root password (e.g. `123456`)
- **Write this password down** — you will need it later
- Click **Next**

**Windows Service screen:**
- Make sure **"Configure MySQL Server as a Windows Service"** is checked
- Make sure **"Start the MySQL Server at System Startup"** is checked
- Click **Next → Execute → Finish**

---

## Step 2 — Install MySQL Workbench

### 2.1 Download Workbench

Go to: https://downloads.mysql.com/archives/workbench/

- Product Version: **8.0.46**
- Operating System: **Microsoft Windows**
- Download the **MSI Installer**

### 2.2 Install Workbench

Run the downloaded file → Next → Next → Install → Finish

### 2.3 Connect to Local MySQL

Open **MySQL Workbench** → Click **+** next to "MySQL Connections" → Fill in:

```
Connection Name: Local
Hostname:        127.0.0.1
Port:            3306
Username:        root
```

Click **Test Connection** → Enter your root password → If you see **"Successfully made the MySQL connection"** → Click **OK** twice.

---

## Step 3 — Create the Database

Open **MySQL Workbench** → Click the **Local** connection → Press `Ctrl + T` to open a new SQL tab.

Paste the following SQL and press **⚡ (Execute)**:

```sql
CREATE DATABASE IF NOT EXISTS crawler_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

---

## Step 4 — Install Python & VS Code

### 4.1 Install Python

Go to: https://www.python.org/downloads/

Download **Python 3.x** → Run the installer.

> ⚠️ **Important:** Check **"Add Python to PATH"** before clicking Install.

Verify installation — open CMD and run:
```
python --version
```

### 4.2 Install VS Code

Go to: https://code.visualstudio.com/

Download and install VS Code → Open VS Code → Press `Ctrl + Shift + X` → Search **Python** → Install the Microsoft Python extension.

---

## Step 5 — Install Required Libraries

Open CMD or VS Code Terminal and run:

```
pip install scrapy mysql-connector-python
```

Wait for **"Successfully installed..."** to appear.

---

## Step 6 — Configure the Project

### 6.1 Clone or Download the Project

```
git clone https://github.com/your-username/crawler_project.git
cd crawler_project
```

### 6.2 Update config.py

Open `config.py` and update your MySQL password:

```python
DB_PASSWORD = "your_mysql_password"   # ← replace with your actual password
```

---

## Step 7 — Run the Crawler

Open VS Code Terminal (`Ctrl + `` `) and run:

```
python main.py
```

You should see output like:

```
Database setup complete!
=== Starting all crawlers ===
Found 30 links on VnExpress
[VnExpress] Saved: Article title here...
=== VnExpress: 30 items saved ===
=== All crawlers finished ===
```

---

## Step 8 — View Data in MySQL Workbench

Open **MySQL Workbench** → Click the **Local** connection → Press `Ctrl + T`.

### View all crawled items:
```sql
USE crawler_db;
SELECT id, website_name, title, field1_name, field1_value, crawled_at
FROM items
LIMIT 20;
```

### View websites list:
```sql
USE crawler_db;
SELECT * FROM websites;
```

### View crawl history:
```sql
USE crawler_db;
SELECT * FROM crawl_logs;
```

### Clear all data (for testing):
```sql
USE crawler_db;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE items;
TRUNCATE TABLE crawl_logs;
TRUNCATE TABLE websites;
SET FOREIGN_KEY_CHECKS = 1;
```

---

## Step 9 — Add a New Website to Crawl

Open `sites/sites.py` and add a new config block:

```python
tuoitre = {
    "name"           : "Tuoi Tre",
    "base_url"       : "https://tuoitre.vn",
    "index_url"      : "https://tuoitre.vn/tin-moi-nhat.htm",
    "category"       : "news",
    "link_selector"  : "a.box-category-item",
    "title_selector" : "h1.article-title",
    "fields"         : {
        "author"  : "span.author-name",
        "content" : "div.detail-content"
    }
}

ALL_SITES = [
    vnexpress,
    tuoitre,   # ← add new site here
]
```

Then run `python main.py` again — it will crawl all sites simultaneously.

---

## How to Find Selectors for a New Website

1. Open the website in Chrome/Edge
2. Press **F12** to open DevTools
3. Click the **cursor icon** (top-left of DevTools)
4. Click on the title / price / author on the webpage
5. Look at the highlighted HTML in DevTools — note the tag and class name

Example: if you see `<h1 class="title-detail">` → selector is `h1.title-detail`

---

## Database Structure

### Table: `websites`
| Column | Description |
|---|---|
| id | Auto-increment ID |
| name | Website name |
| base_url | Website base URL |
| category | Type: news / shopping / books / other |
| created_at | Date added |

### Table: `items`
| Column | Description |
|---|---|
| id | Auto-increment ID |
| website_id | Reference to websites table |
| website_name | Website name (for easy viewing) |
| title | Title of the item / article |
| field1_name | Extra field name (e.g. "author", "price") |
| field1_value | Extra field value |
| field2_name | Extra field name |
| field2_value | Extra field value |
| field3_name | Extra field name |
| field3_value | Extra field value |
| url | Source URL |
| crawled_at | Date crawled |

### Table: `crawl_logs`
| Column | Description |
|---|---|
| id | Auto-increment ID |
| website_id | Reference to websites table |
| website_name | Website name |
| started_at | Crawl start time |
| finished_at | Crawl finish time |
| items_saved | Number of items saved |
| status | success / failed |

---

## Troubleshooting

**`pip` not recognized:**
```
python -m pip install scrapy mysql-connector-python
```

**MySQL connection failed:**
- Make sure MySQL Server is running: open `services.msc` → find **MySQL80** → Start
- Double-check password in `config.py`

**Found 0 links:**
- The website may have changed its HTML structure
- Use F12 to re-check the `link_selector` for that website

**Data not showing in Workbench:**
- Make sure you're querying the `items` table, not `articles`
- Run `python main.py` first to populate the database
