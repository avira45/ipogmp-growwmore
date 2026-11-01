# Growmore IPO GMP Platform 📈

An automated Indian IPO Grey Market Premium (GMP) tracking platform built for **Growmore** (`ipo.growmore`), designed to automatically update daily once per day.

---

## 🚀 Key Features

- **⚡ Automated Daily Sync**: Background scheduler automatically fetches the latest Grey Market Premium data once per day at 09:30 AM IST (configurable).
- **🏢 Subdomain Ready**: Fully branded for Growmore (`ipo.growmore.com` / `ipo.growmore.in`).
- **📊 Real-Time Market Overview**:
  - Open / Active IPOs count
  - Average Expected Listing Gain %
  - Today's Top GMP Gainer
  - SME vs Mainboard breakdown
- **🔍 Filter & Search**:
  - Filter by Category: **Mainboard** vs **SME**
  - Filter by Status: **Open Now**, **Upcoming**, **Closed**
  - Instant live search by IPO company name
  - Sort by GMP %, Issue Price, or Company Name
- **🗂️ Dual Views**: Switch between modern responsive **Cards View** and compact **Table View**.
- **🧮 Interactive Profit Calculator**: Select number of lots applied to immediately calculate:
  - Total Application Amount
  - Expected Listing Gain / Profit (₹)
  - Estimated Total Portfolio Value at listing
- **📜 Historical Archive**: Automatically saves daily JSON snapshots in `data/history/` with a past date selector.
- **🛡️ High Reliability**: Automatic fallback protects against scraper or network drops so the public website never crashes or shows blank data.

---

## 📂 Project Structure

```text
sub finance/
│
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, static mounts, and REST API
│   ├── scraper.py         # Robust live IPO GMP parser & extractor
│   ├── storage.py         # JSON storage, daily history snapshots, and statistics
│   └── scheduler.py       # APScheduler daily once-per-day cron job (09:30 AM)
│
├── static/
│   ├── index.html         # Responsive Growmore frontend
│   ├── css/
│   │   └── style.css      # Dark theme styling, animations & badges
│   └── js/
│       └── app.js         # Reactive filters, profit calculator & API caller
│
├── data/
│   ├── ipos.json          # Today's active IPO GMP database
│   └── history/           # Daily archived historical records (YYYY-MM-DD.json)
│
├── run.py                 # 1-command startup script
├── requirements.txt       # Python dependencies
├── SUBDOMAIN_SETUP.md     # Step-by-step guide to connect ipo.growmore.<domain>
└── README.md
```

---

## 🏃 Quick Start

### 1. Install Dependencies
```bash
py -3 -m pip install -r requirements.txt
```

### 2. Start the Server
```bash
py -3 run.py
```

Open your browser at:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## ⏰ Daily Update Automation

The platform includes an automated background cron runner (`app/scheduler.py` using `APScheduler`):
- Runs automatically **once per day** at **09:30 AM IST**.
- If the server restarts after 09:30 AM, it detects whether today's data is already recorded. If missing, it fetches today's data immediately.
- To trigger a manual sync anytime, click the **"Refresh"** button on the top right of the website or call:
  ```bash
  curl -X POST http://localhost:8000/api/sync
  ```

---

## 🌐 Connecting your Growmore Subdomain

See **[SUBDOMAIN_SETUP.md](SUBDOMAIN_SETUP.md)** for instructions on pointing `ipo.growmore.com` (or `ipo.growmore.in`) using Cloudflare, Nginx, or Docker.
