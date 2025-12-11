from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from ..api import meta, request, dashboard

app = FastAPI()

app.include_router(meta.router)
app.include_router(request.router)
app.include_router(dashboard.router)


CHART_DIR = Path(__file__).resolve().parent.parent / "chart_storage"

templates = Jinja2Templates(directory = "creditcard_analysis/api/templates")

app.mount("/static", StaticFiles(directory = "creditcard_analysis/api/static"), name = "static")
app.mount("/chart_storage", StaticFiles(directory = str(CHART_DIR)), name = "chart_storage")

@app.get("/", response_class = HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chart/{name}")
def get_chart(name: str):
    if "/" in name or "\\" in name:
        raise HTTPException(400, "invalid filename")
    path = CHART_DIR / name
    if not path.exists():
        raise HTTPException(404, "file not found")
    return FileResponse(path, media_type="image/png")    

@app.get("/dashboard", response_class = HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/bar", response_class = HTMLResponse)
def chart_bar(request: Request):
    return templates.TemplateResponse("bar.html", {"request": request})

@app.get("/line", response_class = HTMLResponse)
def chart_line(request: Request):
    return templates.TemplateResponse("line.html", {"request": request})

@app.get("/pie", response_class = HTMLResponse)
def chart_pie(request: Request):
    return templates.TemplateResponse("pie.html", {"request": request})

@app.get("/heatmap", response_class = HTMLResponse)
def chart_heatmap(request: Request):
    return templates.TemplateResponse("heatmap.html", {"request": request})

