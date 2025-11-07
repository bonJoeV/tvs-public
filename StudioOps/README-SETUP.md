# StudioOps Dashboard - Setup Guide

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [File Versions Explained](#file-versions-explained)
- [Local Usage (No Server)](#local-usage-no-server)
- [Server Usage (Recommended)](#server-usage-recommended)
- [Web Hosting Deployment](#web-hosting-deployment)
- [Troubleshooting](#troubleshooting)
- [FAQs](#faqs)

---

## 🎯 Overview

The StudioOps Dashboard comes in **two versions** to accommodate different usage scenarios:

| Version | File | Use Case | Pros | Cons |
|---------|------|----------|------|------|
| **ES6 Modular** | `index.html` | Web server deployment | Fast, maintainable, better caching | Requires web server (CORS) |
| **Bundled** | `dashboard.html` | Local file system | Works with `file://` protocol | Larger file size, no caching |

---

## 🚀 Quick Start

### Option 1: Smart Launcher (Recommended)
The easiest way to get started:

```bash
# Open in your browser
start.html  (Windows: double-click)
open start.html  (Mac)
xdg-open start.html  (Linux)
```

The launcher will:
- ✅ Detect if you're running locally or on a server
- ✅ Provide appropriate instructions
- ✅ Auto-redirect to the best version for your environment

### Option 2: Quick Local Server

```bash
# Start the built-in Python server
python3 server.py

# Then open in your browser:
# http://localhost:8000/
```

---

## 📁 File Versions Explained

### `index.html` - ES6 Modular Version

**Structure:**
```
index.html (main HTML)
├── css/styles.css
└── js/
    ├── main.js (entry point)
    ├── config.js
    ├── utils.js
    ├── data.js
    ├── filters.js
    ├── charts.js
    ├── tabs.js
    ├── upload.js
    ├── settings.js
    ├── modals.js
    └── exports.js
```

**Advantages:**
- 🚀 **Fast Loading**: Browser caches individual modules
- 🛠️ **Easy Maintenance**: Changes affect only specific modules
- 📦 **Smaller Network Transfer**: Only modified files reload
- 🔧 **Better Debugging**: Clear file structure in dev tools

**Requirements:**
- Must be served via HTTP/HTTPS (web server)
- Cannot work with `file://` protocol due to CORS

**Best For:**
- Web hosting (shared hosting, cloud, VPS)
- Local development with server
- Production environments

---

### `dashboard.html` - Bundled Single-File Version

**Structure:**
```
dashboard.html (everything in one file)
├── <style> (all CSS inlined)
└── <script> (all JavaScript inlined)
```

**Advantages:**
- 📂 **File Protocol Compatible**: Works with `file://`
- 🔌 **Fully Offline**: No external dependencies (except CDN libraries)
- 📧 **Easy Sharing**: Single file to email or distribute
- 💾 **Portable**: Copy anywhere and it works

**Trade-offs:**
- Larger file size (~800KB+)
- No browser caching of individual modules
- Harder to customize/debug

**Best For:**
- Opening directly from file system (no server)
- Offline use
- Quick sharing with others
- Backup/archive purposes

---

## 📂 Local Usage (No Server)

If you want to use the dashboard without setting up a server:

### Step 1: Choose the Right File

```bash
# Use dashboard.html for local file access
# Double-click or open with your browser:
dashboard.html
```

### Step 2: Upload Your Data

1. Click the **📁 Upload Data** button in the top-right corner
2. Upload your Momence export files:
   - Payroll ZIP (all employee payroll files)
   - Attendance ZIP (VSP name mapping)
   - Memberships CSV (sales/cancellations)
   - Leads CSV (customers/leads)
   - Leads Converted Report CSV (detailed sources)

### Step 3: Configure Settings

1. Click the **⚙️ Settings** button
2. Set your franchise parameters:
   - Timezone
   - Franchise fee percentage
   - Brand fund percentage
   - CC processing fees
   - Monthly goals
   - Salaried employees (if any)

### Important Notes:

⚠️ **Limitations with File Protocol:**
- ES6 modules (`index.html`) will NOT work
- Must use `dashboard.html` instead
- All data is processed locally in your browser
- No data is sent to any server

---

## 🌐 Server Usage (Recommended)

### Option A: Python Built-in Server (Easiest)

**Requirements:** Python 3.x (usually pre-installed on Mac/Linux)

```bash
# Navigate to the StudioOps directory
cd /path/to/StudioOps

# Start the server (default port 8000)
python3 server.py

# Or specify a custom port
python3 server.py 3000
```

**Then open in your browser:**
```
http://localhost:8000/start.html     (Smart launcher)
http://localhost:8000/index.html     (ES6 version)
http://localhost:8000/dashboard.html (Bundled version)
```

**Stop the server:** Press `Ctrl+C`

---

### Option B: Node.js http-server

**Requirements:** Node.js and npm

```bash
# Install http-server globally (one-time)
npm install -g http-server

# Navigate to directory
cd /path/to/StudioOps

# Start server
http-server -p 8000

# With CORS enabled
http-server -p 8000 --cors
```

---

### Option C: PHP Built-in Server

**Requirements:** PHP 5.4+

```bash
# Navigate to directory
cd /path/to/StudioOps

# Start server
php -S localhost:8000
```

---

### Option D: VS Code Live Server Extension

**If you use Visual Studio Code:**

1. Install the "Live Server" extension
2. Open the StudioOps folder in VS Code
3. Right-click `index.html` or `start.html`
4. Select "Open with Live Server"

---

## 🚀 Web Hosting Deployment

### For Shared Hosting (cPanel, Plesk, etc.)

1. **Upload Files:**
   ```
   Upload entire StudioOps folder via FTP/File Manager
   ```

2. **Set Permissions:**
   ```bash
   # Make sure HTML files are readable
   chmod 644 *.html
   chmod 644 css/*.css
   chmod 644 js/*.js
   ```

3. **Access:**
   ```
   https://yourdomain.com/StudioOps/start.html
   or
   https://yourdomain.com/StudioOps/index.html
   ```

### For Cloud Hosting (AWS, DigitalOcean, etc.)

1. **Upload to web root:**
   ```bash
   # Example for nginx
   sudo cp -r StudioOps /var/www/html/

   # Example for Apache
   sudo cp -r StudioOps /var/www/html/
   ```

2. **Configure web server (if needed):**

   **Nginx:**
   ```nginx
   location /StudioOps {
       index index.html start.html;
       try_files $uri $uri/ =404;
   }
   ```

   **Apache:**
   ```apache
   <Directory "/var/www/html/StudioOps">
       Options Indexes FollowSymLinks
       AllowOverride None
       Require all granted
       DirectoryIndex start.html index.html
   </Directory>
   ```

3. **Security (Optional but recommended):**
   ```bash
   # Restrict access via .htaccess (Apache)
   AuthType Basic
   AuthName "Restricted Access"
   AuthUserFile /path/to/.htpasswd
   Require valid-user
   ```

### For Static Site Hosting (Netlify, Vercel, GitHub Pages)

1. **Create `netlify.toml` or `vercel.json`:**
   ```toml
   # netlify.toml
   [[redirects]]
     from = "/"
     to = "/start.html"
     status = 200
   ```

2. **Deploy:**
   ```bash
   # Using Netlify CLI
   netlify deploy --prod

   # Using Vercel CLI
   vercel --prod

   # Using git (GitHub Pages)
   git add .
   git commit -m "Deploy dashboard"
   git push origin main
   ```

---

## 🔧 Troubleshooting

### Problem: "Failed to load module" error

**Cause:** You're trying to open `index.html` directly with `file://` protocol.

**Solution:**
```bash
# Option 1: Use dashboard.html instead
Open dashboard.html directly

# Option 2: Use a local server
python3 server.py
```

---

### Problem: Blank page or nothing loads

**Possible causes:**

1. **JavaScript disabled:**
   - Enable JavaScript in your browser settings

2. **Browser compatibility:**
   - Use a modern browser (Chrome, Firefox, Safari, Edge)
   - Update to the latest version

3. **CDN libraries blocked:**
   - Check if Chart.js, PapaParse, JSZip are loading
   - Open browser console (F12) to see errors
   - If corporate firewall blocks CDNs, use bundled version

---

### Problem: Data doesn't persist after refresh

**This is normal!** The dashboard processes data locally in your browser.

**To save your work:**
1. Use browser bookmarks
2. Export data to CSV before closing
3. Keep your original Momence files safe
4. Re-upload when needed

**For persistent storage (advanced):**
- Consider using browser localStorage
- Or deploy to a backend with database

---

### Problem: Charts not rendering

**Check:**
1. Data uploaded correctly (check browser console)
2. Chart.js CDN is accessible
3. No JavaScript errors in console

**Fix:**
```javascript
// Open browser console (F12) and check for errors
// Common issue: Check network tab for failed CDN requests
```

---

### Problem: Slow performance with large datasets

**Tips:**
1. Filter data to specific date ranges
2. Use Chrome or Edge (fastest JS engines)
3. Close other browser tabs
4. Increase available browser memory
5. Consider splitting data into smaller time periods

---

## ❓ FAQs

### Q: Which version should I use?

**A:**
- **Local file access (no server):** Use `dashboard.html`
- **Local with server:** Use `index.html` (faster, better experience)
- **Web hosting:** Use `index.html`
- **Offline/portable:** Use `dashboard.html`
- **Not sure:** Use `start.html` (smart launcher will help)

---

### Q: Is my data sent to any server?

**A:** No! All data processing happens locally in your browser. Nothing is uploaded to external servers except:
- CDN libraries (Chart.js, PapaParse, JSZip) are loaded from CDNs
- Your uploaded CSV/ZIP files stay in browser memory only
- Settings are saved to browser's localStorage

---

### Q: Can I customize the dashboard?

**A:** Yes!

**For ES6 version (`index.html`):**
- Edit individual `.js` files in the `js/` folder
- Modify `css/styles.css` for styling
- Changes are modular and maintainable

**For bundled version (`dashboard.html`):**
- Edit the single file (search for `<script>` or `<style>` sections)
- Harder to maintain but works offline

---

### Q: How do I update to a newer version?

**A:**
1. Backup your current files
2. Download/extract new version
3. Copy over any custom modifications
4. Test with sample data first
5. Re-upload your data files

**Note:** Settings and data are not automatically migrated.

---

### Q: Can I host this on WordPress/Shopify/Wix?

**A:** It depends:

**WordPress:**
- ✅ Yes, use a file manager plugin or FTP
- Upload to `/wp-content/dashboard/`

**Shopify:**
- ⚠️ Limited - use external hosting and iframe

**Wix:**
- ⚠️ Limited - upload as static files or use iframe

**Best approach:** Use proper web hosting for full control

---

### Q: What browsers are supported?

**A:** Modern browsers with ES6 support:
- ✅ Chrome/Chromium 60+
- ✅ Firefox 60+
- ✅ Safari 12+
- ✅ Edge 79+
- ❌ Internet Explorer (not supported)

---

### Q: Can I use this offline?

**A:** Yes! Use `dashboard.html`:
1. Download the entire StudioOps folder
2. Open `dashboard.html` in your browser
3. All processing is local
4. Note: CDN libraries (Chart.js, etc.) require internet on first load
   - After first load, they may be cached

**For true offline use:**
- Download Chart.js, PapaParse, JSZip locally
- Update CDN links to local paths in HTML

---

### Q: How do I share this with my team?

**Options:**

1. **Web Hosting (Recommended):**
   - Deploy to shared hosting
   - Share the URL
   - Add password protection if needed

2. **File Sharing:**
   - Send `dashboard.html` via email
   - Recipients open it locally
   - Each person uploads their own data

3. **Internal Server:**
   - Host on company intranet
   - Access via internal network

---

## 📞 Support

For issues, questions, or contributions:

1. Check this README first
2. Look at browser console for errors (F12)
3. Review the main README.md file
4. Check the modular documentation (README-MODULAR.md)

---

## 🎉 You're All Set!

Congratulations! You should now have a working StudioOps Dashboard.

**Quick recap:**
- 📂 Local use: `dashboard.html`
- 🌐 Server use: `index.html` (via `python3 server.py`)
- 🚀 Smart launcher: `start.html`

**Happy analyzing!** 📊
