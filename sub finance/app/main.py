async def robots(request: Request = None):
    host = "ipo.growwmore.in"
    proto = "https"
    if request:
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "ipo.growwmore.in"
        proto = request.headers.get("x-forwarded-proto") or "https"
    base_url = f"{proto}://{host}"
    txt_content = f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n"
    return Response(content=txt_content, media_type="text/plain")
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
async def catch_all_fallback(request: Request, full_path: str):
    if "sitemap.xml" in full_path:
        return await sitemap(request)
    if "robots.txt" in full_path:
        return await robots(request)
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
