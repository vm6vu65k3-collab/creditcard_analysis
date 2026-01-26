# 信用卡消費分析

以「信用卡消費資料」為主題的資料工程與分析專案：從公開資料下載 CSV，完成資料清理與 ETL 入庫（SQLAlchemy），\
並提供 API 與圖表/儀表板呈現（FastAPI + ECharts），支援查詢條件、趨勢分析、TopN、占比與成長率計算，以及圖表結果快取。

## 功能 

### ETL 流程
- 下載公開資料 CSV（timeout / stream）
- 自訂 SSL Context（避免環境憑證驗證問題）
- 缺失值及重複值處理
- 欄位標準化處理，確保寫入資料庫一致性
- 透過 SQLAlchemy ORM + Alembic migrations 管理資料庫結構
- 支援匯總分析：Raw SQL / SQLAlchemy Session Query 

### API 與分析 
- FastAPI 提供圖表查詢端點
- 支援 bar / line / pie / heatmap 四種圖表

### 圖表快取
- 將輸入參數序列化成 JSON，並以 hash 生成 `cache_key`
- ChartRequest / ChartResult 紀錄查詢結果與狀態（命中相同 `cache_key` 則回傳既有結果）

### 分析儀表板
- ECharts 呈現趨勢、當月排行、各產業排行
- 支援年月區間、產業別、年齡層篩選


## 快速執行

### 前置條件
- 已安裝 Python 3.13 
- 已安裝並啟動 MySQL( 建議 8.x)
- 已建立資料庫 `your_db`，並具備可連線的帳號/密碼(對應 `.env` 設定)

### 1. 取得專案
```bash
git clone https://github.com/vm6vu65k3-collab/creditcard_analysis.git
cd creditcard_analysis
```
### 2. 建立與啟用虛擬環境 
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
### 3. 設定環境變數(MySQL)
```bash
# 本專案透過 .env 讀取 MySQL 連線資訊
cp .env.example .env
#請編輯 .env，填入你的 MySQL 連線設定 (.env 請勿提交到 GitHub)
```
### 4. 套用資料庫 Migration
```bash
alembic upgrade head
```
### 5. 執行ETL流程
```bash
python -m creditcard_analysis.clean_data.clean --source csv_url
```
### 6. 啟動API Server
```bash
uvicorn creditcard_analysis.main:app --reload
```
## 入口
- Swagger UI：http://127.0.0.1:8000/docs
- Dashboard：http://127.0.0.1:8000/dashboard
