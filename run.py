import uvicorn
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"🚀 Starting Growmore IPO GMP Platform on http://localhost:{port}")
    print(f"🌐 Configured Subdomain: ipo.growmore")
    print(f"⏰ Daily Auto-sync: Scheduled once per day at 09:30 AM")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
