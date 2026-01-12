from pathlib import Path 
from fastapi import FastAPI, Request 
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routers import request, meta, dashboard

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC = BASE_DIR / 'api/static'
TEMPLATES = BASE_DIR / 'api/templates'
CHART_STORAGE = BASE_DIR / 'chart_storage'

app = FastAPI()
templates = Jinja2Templates(directory = str(TEMPLATES))

app.mount('/static', StaticFiles(directory = str(STATIC)), name = 'static')
app.mount('/chart_storage', StaticFiles(directory = str(CHART_STORAGE)), name = 'chart_storage')

@app.get("/", response_class = HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.get("/bar", response_class = HTMLResponse)
def bar_chart(request: Request):
    return templates.TemplateResponse('bar.html', {'request': request})

@app.get("/line", response_class = HTMLResponse)
def line_chart(request: Request):
    return templates.TemplateResponse('line.html', {'request': request})

@app.get("/pie", response_class = HTMLResponse)
def pie_chart(request: Request):
    return templates.TemplateResponse('pie.html', {'request': request})

@app.get("/heatmap", response_class = Request)
def heatmap_chart(request: Request):
    return templates.TemplateResponse('heatmap.html', {'request': request})

@app.get("/dashboard", response_class = Request)
def dashboard_chart(request: Request):
    return templates.TemplateResponse('dashboard.html', {'request': request})

app.include_router(request.router)
app.include_router(meta.router)
app.include_router(dashboard.router)
