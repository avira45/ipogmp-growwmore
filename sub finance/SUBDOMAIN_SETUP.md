# Subdomain Setup Guide: `ipo.growmore.com`

This guide explains how to connect your **Growmore** domain so that visitors accessing `ipo.growmore.com` (or `ipo.growmore.in`) land directly on your IPO GMP platform.

---

## Architecture Overview

```mermaid
flowchart LR
    A["Public Visitor"] -->|Visits ipo.growmore.com| B["DNS Provider / Cloudflare"]
    B -->|Routes traffic (SSL)| C["Your Server (Port 8000)"]
    C --> D["Growmore IPO GMP Platform"]
```

---

## Method 1: Cloudflare Tunnel (Recommended - Free & Easiest)

Cloudflare Tunnels allow you to expose your local or VPS server securely without opening ports or configuring SSL certificates manually.

1. **Install Cloudflared** on your server:
   ```bash
   winget install Cloudflare.cloudflared
   ```
2. **Login to your Cloudflare account**:
   ```bash
   cloudflared tunnel login
   ```
3. **Create a tunnel**:
   ```bash
   cloudflared tunnel create growmore-ipo
   ```
4. **Point your subdomain**:
   In your Cloudflare DNS dashboard:
   - Type: `CNAME`
   - Name: `ipo` (or `gmp`)
   - Target: `<TUNNEL_ID>.cfargotunnel.com`
   - Proxy status: **Proxied (Orange Cloud)**
5. **Route traffic to the application**:
   ```bash
   cloudflared tunnel run --url http://localhost:8000 growmore-ipo
   ```
   Done! Your site is now live at `https://ipo.growmore.com` with free automated HTTPS/SSL.

---

## Method 2: Standard DNS + Nginx Reverse Proxy (Linux VPS / Cloud)

If running on a VPS (Ubuntu / Debian / AWS / DigitalOcean / Linode):

### 1. DNS Record
In your domain registrar (GoDaddy, Namecheap, Cloudflare, Google Domains):
- **Type**: `A`
- **Host / Name**: `ipo`
- **Value / Points to**: Your VPS Public IPv4 Address (e.g. `203.0.113.195`)
- **TTL**: Auto / 300s

### 2. Nginx Configuration
Create `/etc/nginx/sites-available/ipo.growmore.com`:
```nginx
server {
    server_name ipo.growmore.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site and obtain free SSL:
```bash
sudo ln -s /etc/nginx/sites-available/ipo.growmore.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d ipo.growmore.com
```

---

## Method 3: Running as a Persistent Background Service

### On Windows:
Use NSSM (Non-Sucking Service Manager) or PM2:
```bash
# Using PM2
npm install -g pm2
pm2 start "py -3 run.py" --name "growmore-ipo-gmp"
pm2 save
pm2 startup
```

### On Linux (systemd):
Create `/etc/systemd/system/growmore-ipo.service`:
```ini
[Unit]
Description=Growmore IPO GMP Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/growmore-ipo
ExecStart=/usr/bin/python3 run.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Start and enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable growmore-ipo
sudo systemctl start growmore-ipo
```

---

## Verification
Once configured, visit:
`https://ipo.growmore.com`
The Growmore IPO GMP platform will load with live data and auto-updates enabled.
