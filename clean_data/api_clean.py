import io
import ssl
import httpx
from fastapi import FastAPI, HTTPException 
from fastapi.responses import StreamingResponse

app = FastAPI()

UPSTREAM_BASE = "https://bas.nccc.com.tw/nccc-nop"

def build_sql_context():
    ctx = ssl.create_default_context(cafile = "/etc/ssl/cert.pem")
    if hasattr(ctx, "verify_flags") and hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx 

SSL_CTX = build_sql_context()

@app.get("/OpenAPI/C02/ageconsumption/{regionCode}/{industryCode}")
async def proxy_ageconsumption(regionCode: str, industryCode: str):
    url = f"{UPSTREAM_BASE}/OpenAPI/C02/ageconsumption/{regionCode}/{industryCode}"
    
    try:
        async with httpx.AsyncClient(timeout = 60, verify = SSL_CTX, follow_redirects = True) as client:
            r = await client.get(url, headers = {"accept": "application/octet-stream"})
    except httpx.HTTPError as e:
        raise HTTPException(status_code = 502, detail = f"Upstream request failed: {e!s}")
    
    if r.status_code != 200:
        raise HTTPException(status_code = r.status_code, detail = r.text)
    
    if not r.content:
        raise HTTPException(status_code = 404, detail = "No data(empty file).")

    headers = {}
    cd = r.headers.get("content-disposition")
    if cd:
        headers["Content-Disposition"] = cd

    return StreamingResponse(
        io.BytesIO(r.content),
        media_type = r.headers.get("content-type", "application/octet-stream"),
        headers = headers
    )