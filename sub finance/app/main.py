import os
import sys
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

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
    description="Live Open IPO Grey Market Premium Tracker for Growmore",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_html_content() -> str:
    """Read index.html content reliably across all deployment environments."""
    search_paths = [
        os.path.join(BASE_DIR, "index.html"),
        os.path.join(STATIC_DIR, "index.html"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "index.html"),
    ]
    for path in search_paths:
        if os.path.exists(path) and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    return "<h1>Growmore IPO GMP</h1><p>Loading IPO rates...</p>"

# Mount static files if directory exists
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/api/ipos")
async def get_ipos(
    category: Optional[str] = Query(None, description="mainboard, sme, or all"),
    search: Optional[str] = Query(None, description="Search by company name"),
    sort_by: Optional[str] = Query("gmp_pct_desc")
):
    """Retrieve list of currently open IPOs with filters and sorting."""
    data = load_ipos()
    ipos = [i for i in data.get("ipos", []) if i.get("status") == "Open"]

    if category and category.lower() != "all":
        ipos = [i for i in ipos if i.get("category", "").lower() == category.lower()]

    if search:
        search_lower = search.lower().strip()
        ipos = [i for i in ipos if search_lower in i.get("name", "").lower()]

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
        "ipos": ipos
    }

@app.get("/api/stats")
async def get_stats():
    """Get market summary statistics for open IPOs."""
    data = load_ipos()
    return {
        "brand": data.get("brand", "Growmore"),
        "subdomain": data.get("subdomain", "ipo.growmore"),
        "stats": data.get("stats", {})
    }

@app.get("/data/ipos.json")
async def get_raw_ipos_json():
    """Direct static data endpoint."""
    return load_ipos()

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "Growmore IPO GMP Tracker"}

# Handle every homepage and rewritten path without 404
@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def serve_index_html():
    return HTMLResponse(content=get_html_content(), status_code=200)

# Global catch-all fallback: Prevents any '{"detail":"Not Found"}' on Vercel
@app.api_route("/{full_path:path}", methods=["GET"])
async def catch_all_fallback(full_path: str):
    if full_path.endswith("api/ipos") or full_path == "api/ipos":
        return await get_ipos()
    if full_path.endswith("api/stats") or full_path == "api/stats":
        return await get_stats()
    if full_path.endswith("data/ipos.json"):
        return load_ipos()

    # Serve static assets if matched
    clean_path = full_path.replace("static/", "", 1)
    file_candidate = os.path.join(STATIC_DIR, clean_path)
    if os.path.exists(file_candidate) and os.path.isfile(file_candidate):
        return FileResponse(file_candidate)

    # Return homepage HTML
    return HTMLResponse(content=get_html_content(), status_code=200)
