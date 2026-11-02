import json
import os
import datetime
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
HISTORY_DIR = os.path.join(DATA_DIR, 'history')
DATA_FILE = os.path.join(DATA_DIR, 'ipos.json')

os.makedirs(HISTORY_DIR, exist_ok=True)

def parse_date_safe(date_str: str, default_year: int = None) -> Optional[datetime.date]:
    """Parse date string like '2-Nov' or '30-Oct' into a datetime.date object."""
    if not date_str or str(date_str).strip() in ['--', '-', '']:
        return None
    if default_year is None:
        default_year = datetime.datetime.now().year
    try:
        parts = str(date_str).strip().split('-')
        if len(parts) == 2:
            day = int(parts[0])
            month_str = parts[1]
            return datetime.datetime.strptime(f"{day}-{month_str}-{default_year}", "%d-%b-%Y").date()
    except Exception:
        pass
    return None

def filter_open_ipos(ipos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Keep IPOs on the tracker until their Listing Date has passed.
    Once listed (listing date < today), the IPO is removed.
    """
    today = datetime.date.today()
    active = []

    for i in ipos:
        list_dt = parse_date_safe(i.get('listing_date'))
        close_dt = parse_date_safe(i.get('close_date'))
        allot_dt = parse_date_safe(i.get('allotment_date'))
        status = i.get('status', 'Open')

        # Check if already listed in the past
        if list_dt and list_dt < today:
            continue

        # Set human-readable stage badge
        if list_dt and list_dt == today:
            i['stage'] = 'Listing Today'
        elif close_dt and close_dt < today:
            if allot_dt and allot_dt <= today:
                i['stage'] = 'Allotted'
            else:
                i['stage'] = 'Closed'
        elif status == 'Open':
            i['stage'] = 'Open'
        else:
            i['stage'] = status

        active.append(i)

    return active

def save_ipos(ipos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Save scraped IPOs to primary JSON and daily archive."""
    if not ipos:
        logger.warning("Empty IPO list received; skipping save to avoid overwriting.")
        return load_ipos()

    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Only keep Open IPOs
    open_ipos = filter_open_ipos(ipos)

    # Calculate stats based on open IPOs
    stats = compute_stats(open_ipos, timestamp_str)

    data_payload = {
        "brand": "Growmore",
        "subdomain": "ipo.growmore",
        "last_updated": timestamp_str,
        "date": today_str,
        "stats": stats,
        "ipos": open_ipos,
        "raw_count": len(ipos)
    }

    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_payload, f, indent=2, ensure_ascii=False)
        
        archive_file = os.path.join(HISTORY_DIR, f"{today_str}.json")
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(data_payload, f, indent=2, ensure_ascii=False)

        logger.info("Saved %d OPEN IPOs to %s", len(open_ipos), DATA_FILE)
    except Exception as e:
        logger.error("Error saving IPO data: %s", e)

    return data_payload

def load_ipos() -> Dict[str, Any]:
    """Load current IPO data from file, keeping only Open IPOs."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "ipos" in data:
                    data["ipos"] = filter_open_ipos(data["ipos"])
                return data
        except Exception as e:
            logger.error("Error loading %s: %s", DATA_FILE, e)

    return {
        "brand": "Growmore",
        "subdomain": "ipo.growmore",
        "last_updated": None,
        "date": None,
        "stats": {},
        "ipos": []
    }

def compute_stats(ipos: List[Dict[str, Any]], timestamp: str) -> Dict[str, Any]:
    """Compute market summary statistics for open IPOs."""
    total = len(ipos)
    if total == 0:
        return {}

    open_ipos = [i for i in ipos if i.get('status') == 'Open']
    sme_ipos = [i for i in ipos if i.get('category') == 'SME']
    mainboard_ipos = [i for i in ipos if i.get('category') == 'Mainboard']

    valid_gains = [i.get('gmp_percentage', 0.0) for i in ipos if i.get('gmp_percentage', 0.0) > 0]
    avg_gain = round(sum(valid_gains) / len(valid_gains), 1) if valid_gains else 0.0

    sorted_by_gain = sorted(ipos, key=lambda x: x.get('gmp_percentage', 0.0), reverse=True)
    top_gainer = None
    if sorted_by_gain and sorted_by_gain[0].get('gmp_percentage', 0.0) > 0:
        top = sorted_by_gain[0]
        top_gainer = {
            "name": top.get('name'),
            "gmp": top.get('gmp'),
            "gmp_percentage": top.get('gmp_percentage'),
            "category": top.get('category')
        }

    return {
        "total_ipos": total,
        "open_count": len(open_ipos),
        "sme_count": len(sme_ipos),
        "mainboard_count": len(mainboard_ipos),
        "avg_gain_percentage": avg_gain,
        "top_gainer": top_gainer,
        "last_updated": timestamp
    }

def get_history_dates() -> List[str]:
    """Get list of past archived dates."""
    if not os.path.exists(HISTORY_DIR):
        return []
    files = [f.replace('.json', '') for f in os.listdir(HISTORY_DIR) if f.endswith('.json')]
    return sorted(files, reverse=True)

def get_history_by_date(date_str: str) -> Optional[Dict[str, Any]]:
    """Retrieve historical data for a specific date (YYYY-MM-DD)."""
    file_path = os.path.join(HISTORY_DIR, f"{date_str}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error reading history file %s: %s", file_path, e)
    return None
