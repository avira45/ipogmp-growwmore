import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.storage import load_ipos, get_history_dates, get_history_by_date
from app.scheduler import start_scheduler, shutdown_scheduler, sync_daily_gmp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler only in persistent server environments (not in Vercel serverless)
    if not os.environ.get("VERCEL"):
        start_scheduler(hour=9, minute=30)
    yield
    if not os.environ.get("VERCEL"):
        shutdown_scheduler()

app = FastAPI(
    title="Growmore IPO GMP Tracker",
    description="Automated Daily IPO Grey Market Premium Tracker for Growmore (ipo.growmore)",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for subdomain and multi-domain access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=FileResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/api/ipos")
async def get_ipos(
    category: Optional[str] = Query(None, description="mainboard, sme, or all"),
    status: Optional[str] = Query(None, description="open, upcoming, closed, or all"),
    search: Optional[str] = Query(None, description="Search by company name"),
    sort_by: Optional[str] = Query("gmp_pct_desc", description="Sort option: gmp_pct_desc, gmp_pct_asc, price_desc, price_asc, name")
):
    """Retrieve list of IPOs with optional filters and sorting."""
    data = load_ipos()
    ipos = data.get("ipos", [])

    # Filter Category
    if category and category.lower() != "all":
        ipos = [i for i in ipos if i.get("category", "").lower() == category.lower()]

    # Filter Status
    if status and status.lower() != "all":
        ipos = [i for i in ipos if i.get("status", "").lower() == status.lower()]

    # Filter Search
    if search:
        search_lower = search.lower().strip()
        ipos = [i for i in ipos if search_lower in i.get("name", "").lower()]

    # Sorting
    if sort_by == "gmp_pct_desc":
        ipos = sorted(ipos, key=lambda x: x.get("gmp_percentage", 0.0), reverse=True)
    elif sort_by == "gmp_pct_asc":
        ipos = sorted(ipos, key=lambda x: x.get("gmp_percentage", 0.0))
    elif sort_by == "price_desc":
        ipos = sorted(ipos, key=lambda x: x.get("price", 0.0), reverse=True)
    elif sort_by == "price_asc":
        ipos = sorted(ipos, key=lambda x: x.get("price", 0.0))
    elif sort_by == "name":
        ipos = sorted(ipos, key=lambda x: x.get("name", "").lower())

    return {
        "brand": data.get("brand", "Growmore"),
        "subdomain": data.get("subdomain", "ipo.growmore"),
        "last_updated": data.get("last_updated"),
        "date": data.get("date"),
        "count": len(ipos),
        "total_available": len(data.get("ipos", [])),
        "ipos": ipos
    }

@app.get("/api/stats")
async def get_stats():
    """Get market overview statistics."""
    data = load_ipos()
    return {
        "brand": data.get("brand", "Growmore"),
        "subdomain": data.get("subdomain", "ipo.growmore"),
        "last_updated": data.get("last_updated"),
        "stats": data.get("stats", {})
    }

@app.post("/api/sync")
async def trigger_manual_sync():
    """Trigger an immediate scrape and update."""
    result = sync_daily_gmp(force=True)
    return result

@app.get("/api/history")
async def list_history():
    """List all available past snapshot dates."""
    dates = get_history_dates()
    return {"dates": dates}

@app.get("/api/history/{date}")
async def get_history(date: str):
    """Get historical snapshot for a specific date (YYYY-MM-DD)."""
    snapshot = get_history_by_date(date)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No historical record found for this date.")
    return snapshot

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "Growmore IPO GMP Tracker"}
