import requests
from bs4 import BeautifulSoup
import re
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'no-cache',
}

PRIMARY_URL = "https://www.investorgain.com/report/live-ipo-gmp/331/"

def clean_number(text: str) -> float:
    """Extract first numeric or float value from string."""
    if not text:
        return 0.0
    text = text.replace(',', '').replace('₹', '').strip()
    match = re.search(r'[-+]?\d*\.?\d+', text)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0

def clean_int(text: str) -> int:
    """Extract integer value from string."""
    val = clean_number(text)
    return int(val)

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def fetch_live_ipo_gmp():
    """Scrape and parse live IPO GMP data from primary source."""
    logger.info("Fetching live IPO GMP data from %s", PRIMARY_URL)
    try:
        response = requests.get(PRIMARY_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logger.error("Failed to fetch IPO data: %s", e)
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    if not table:
        logger.warning("No table found in response.")
        return []

    tbody = table.find('tbody')
    if not tbody:
        rows = table.find_all('tr')[1:]
    else:
        rows = tbody.find_all('tr')

    ipos = []
    current_year = datetime.datetime.now().year

    for tr in rows:
        cells = tr.find_all('td')
        if len(cells) < 8:
            continue

        try:
            # 0: Name cell
            name_cell = cells[0]
            link = name_cell.find('a')
            name = link.get_text(strip=True) if link else name_cell.get_text(strip=True)
            
            # Badges inside name cell
            badges = [b.get_text(strip=True) for b in name_cell.find_all('span')]
            badge_text = " ".join(badges)
            
            # Detect category: Mainboard vs SME
            is_sme = 'SME' in badge_text.upper() or 'SME' in name.upper()
            category = "SME" if is_sme else "Mainboard"

            # Detect exchange
            if 'BSE' in badge_text.upper() and 'NSE' in badge_text.upper():
                exchange = "NSE/BSE"
            elif 'BSE' in badge_text.upper():
                exchange = "BSE"
            else:
                exchange = "NSE"

            # Detect status
            # U = Upcoming, O = Open, C = Closed
            status = "Upcoming"
            for b in badges:
                b_up = b.upper()
                if b_up == 'O' or 'OPEN' in b_up:
                    status = "Open"
                    break
                elif b_up == 'C' or 'CLOSED' in b_up:
                    status = "Closed"
                    break
                elif b_up == 'U' or 'UPCOMING' in b_up:
                    status = "Upcoming"
                    break

            # 1: GMP cell
            gmp_cell = cells[1]
            gmp_text = gmp_cell.get_text(" ", strip=True)
            
            # Extract GMP value
            # e.g., "₹ 5 (5.32%) 5 ↓ / 5 ↑" or "₹ -- (0.00%)"
            gmp_val = 0.0
            gmp_match = re.search(r'₹\s*([-+]?\d*\.?\d+)', gmp_text)
            if gmp_match:
                gmp_val = float(gmp_match.group(1))
            elif '--' not in gmp_text:
                gmp_val = clean_number(gmp_text)

            # Percentage
            pct_val = 0.0
            pct_match = re.search(r'\(([-+]?\d*\.?\d+)%\)', gmp_text)
            if pct_match:
                pct_val = float(pct_match.group(1))

            # Trend low / high
            trend_low = gmp_val
            trend_high = gmp_val
            trend_match = re.search(r'(\d+)\s*↓\s*/\s*(\d+)\s*↑', gmp_text)
            if trend_match:
                trend_low = float(trend_match.group(1))
                trend_high = float(trend_match.group(2))

            # 2: Rating
            rating_cell = cells[2]
            fire_count = rating_cell.get_text().count('🔥')

            # 3: Subscription
            sub_text = cells[3].get_text(strip=True) if len(cells) > 3 else "-"
            if sub_text == '' or sub_text == '--':
                sub_text = "-"

            # 4: Price
            price_text = cells[4].get_text(strip=True) if len(cells) > 4 else "0"
            price = clean_number(price_text)

            # 5: IPO Size
            size_text = cells[5].get_text(strip=True) if len(cells) > 5 else "-"
            if not size_text.startswith('₹') and size_text != '-':
                size_text = f"₹{size_text}"

            # 6: Lot
            lot_text = cells[6].get_text(strip=True) if len(cells) > 6 else "1"
            lot_size = clean_int(lot_text) or 1

            # Dates
            open_date = cells[7].get_text(strip=True) if len(cells) > 7 else "-"
            close_date = cells[8].get_text(strip=True) if len(cells) > 8 else "-"
            allotment_date = cells[9].get_text(strip=True) if len(cells) > 9 else "-"
            listing_date = cells[10].get_text(strip=True) if len(cells) > 10 else "-"
            updated_text = cells[11].get_text(strip=True) if len(cells) > 11 else ""

            # Clean trailing text from dates
            open_date = re.sub(r'GMP.*$', '', open_date).strip() or "-"
            close_date = re.sub(r'GMP.*$', '', close_date).strip() or "-"
            allotment_date = re.sub(r'GMP.*$', '', allotment_date).strip() or "-"
            listing_date = re.sub(r'GMP.*$', '', listing_date).strip() or "-"

            # Derived calculations
            est_listing_price = round(price + gmp_val, 2)
            if price > 0 and pct_val == 0.0 and gmp_val != 0:
                pct_val = round((gmp_val / price) * 100, 2)

            min_investment = round(price * lot_size, 2)
            est_profit_per_lot = round(gmp_val * lot_size, 2)

            ipo_entry = {
                "id": slugify(name),
                "name": name,
                "category": category,
                "exchange": exchange,
                "status": status,
                "price": price,
                "price_text": f"₹{price:g}" if price > 0 else "TBA",
                "gmp": gmp_val,
                "gmp_percentage": pct_val,
                "est_listing_price": est_listing_price,
                "gmp_trend_low": trend_low,
                "gmp_trend_high": trend_high,
                "rating": fire_count,
                "subscription": sub_text,
                "ipo_size": size_text,
                "lot_size": lot_size,
                "min_investment": min_investment,
                "est_profit_per_lot": est_profit_per_lot,
                "open_date": open_date,
                "close_date": close_date,
                "allotment_date": allotment_date,
                "listing_date": listing_date,
                "updated_at": updated_text or datetime.datetime.now().strftime("%d-%b %H:%M"),
            }
            ipos.append(ipo_entry)

        except Exception as row_err:
            logger.debug("Error parsing row: %s", row_err)
            continue

    logger.info("Successfully parsed %d live IPOs", len(ipos))
    return ipos

if __name__ == '__main__':
    results = fetch_live_ipo_gmp()
    print(f"Total parsed: {len(results)}")
    if results:
        print("First IPO:", results[0])
