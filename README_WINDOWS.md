# Short Drama Discovery Platform

A Django 5.2 + MySQL 8.0 starter project for a short-drama discovery directory.
The first version stores drama metadata and links to verified official/authorized viewing pages. It does **not** download, proxy, embed, or host third-party videos.

## 1. Requirements

- Windows 10/11
- Python 3.12 (select the 64-bit installer and enable "Add Python to PATH")
- MySQL Community Server 8.0
- PyCharm

## 2. Create database

Open MySQL Workbench or MySQL command line and execute:

```sql
CREATE DATABASE short_drama_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Create a dedicated database user for a real deployment. For local development, you may use your existing local MySQL user.

## 3. Install dependencies

Extract the ZIP, open the `short_drama_platform` folder in PyCharm, then open its Terminal:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Alternatively, double-click `scripts\setup_windows.bat` to create the venv and install packages.

## 4. Configure database credentials

Copy `.env.example` to `.env` and edit the values. Django automatically loads this file from the project directory. Existing environment variables in PyCharm or Windows take precedence:

- `DB_NAME=short_drama_db`
- `DB_USER=your_mysql_user`
- `DB_PASSWORD=your_mysql_password`
- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`

You can also set environment variables in PyCharm: Run > Edit Configurations > Environment variables. Restart Django after editing `.env`.

## 5. Initialize Django

```powershell
python manage.py check
python manage.py makemigrations core drama advertising analytics
python manage.py migrate
python manage.py createsuperuser
```

## 6. Run

```powershell
python manage.py runserver
```

Open:

- Website: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## 7. Add initial content

1. Sign in to `/admin/`.
2. Add one or more categories (for example Romance, Revenge, Fantasy).
3. Add a drama and set its status to **Published**.
4. Upload a cover image only if you own it or have permission to use it.
5. Add `Drama links` inline. Mark a link as **official/authorized** only after verifying the rights and destination.
6. Add a Site Setting row to set the site name, contact email and optional GA4 Measurement ID.
7. Add Ad Position rows and paste only ad code issued by your own advertising account. Ad positions are a configuration registry in this starter; placement rendering can be customized after ad policy review.

## 8. PyCharm interpreter

Settings > Project > Python Interpreter > Add Interpreter > Existing environment, then select:

`<project folder>\.venv\Scripts\python.exe`

## 9. Included features

- Public home, category, search, drama list and detail pages
- Django Admin CRUD for drama, categories, source links, ad positions and site settings
- Rights metadata fields (rights status, rights holder, scope and expiry)
- SEO title/description, canonical URL, robots.txt and sitemap.xml
- GA4 global tag support when a Measurement ID is configured
- Tracked outbound clicks through `/go/<id>/`
- Responsive Bootstrap 5 templates

## 10. Important limitations before production

- This is a runnable MVP starter, not a finished multi-tenant SaaS.
- No automated scraping or third-party video downloading is included.
- A plain outbound link is not a universal copyright safe harbor. Verify that each destination is official/authorized, use licensed artwork, provide a takedown contact and remove disputed content promptly.
- AdSense approval is not guaranteed. Thin, copied or low-value directory pages may not qualify. Publish substantial original descriptions and follow Google publisher policies.
- GA4 and advertising cookies/identifiers may require a privacy notice and consent mechanism depending on visitor location. Add a compliant consent platform before production where required.
- Before production: set `DEBUG=0`, use a strong secret key, configure HTTPS, secure cookies, allowed hosts, backups, logging, rate limiting and a production web server.
- `ads.txt` intentionally contains no publisher ID. Add only the exact authorized line supplied by your ad network.

## 11. Common Windows issues

### `Access denied for user`
Check MySQL username/password, host and port. Confirm the database exists.

### MySQL service is not running
Open Windows Services and start the MySQL80 service (service name may differ).

### `No module named MySQLdb`
This project uses PyMySQL and registers it in `config/__init__.py`. Ensure the project interpreter is the `.venv` interpreter and reinstall requirements.

### Pillow/image upload errors
Run `pip install Pillow` inside the active virtual environment.

### Static files do not load
During development, confirm `DEBUG=1` and that `static/css/site.css` exists. Production requires `collectstatic` and web-server static configuration.
