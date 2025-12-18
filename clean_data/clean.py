import requests
import certifi
import pandas as pd 
from pathlib import Path
from datetime import datetime 
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.mysql import insert as mysql_insert
from utils import handling_missing_value, handling_duplicate_value
from database import engine

OPEN_DATA_CSV_URL = "https://www.nccc.com.tw/dataDownload/Age%20Group/BANK_TWN_ALL_AG.CSV"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "open_data_downloads"

#下載csv資料
def download_csv(url: str, save_dir: Path) -> Path:
    save_dir.mkdir(parents = True, exist_ok = True)
    
    today = datetime.today().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"raw_open_data{today}.csv"
    try:
        with requests.get(url, timeout =(10, 60), verify = certifi.where(), stream = True) as resp:
            resp.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
    except requests.exceptions.RequestException as e:
        if file_path.exists():
            file_path.unlink(missing_ok = True)
        raise RuntimeError(f"下載失敗：{e}") from e

    print(f"[INFO] CSV 已下載到：{file_path}")
    return file_path

#載入及清理資料
def load_and_clean_csv(csv_path: Path) -> pd.DataFrame:
    
    df = pd.read_csv(
        csv_path,
        encoding = "utf-8-sig",
        na_values = ["", " ", "Na", "NaN"]
    )

    #標準化欄位處理
    columns = ['ym', 'nation', 'industry', 'age_level', 'trans_count', 'trans_total']
    if len(df.columns) != len(columns):
        raise ValueError(f"欄位數不符，原始欄位數{len(df.columns)} 預期欄位{len(columns)}")
        

    df.columns = columns
    print("標準化欄位", df.columns.tolist())

    #缺失及重複值處理
    num_cols = ['trans_count', 'trans_total']
    str_cols = ['ym', 'nation', 'industry', 'age_level']
    df = handling_missing_value(df, num_cols, str_cols)
    df = handling_duplicate_value(df)

    #資料型態轉換
    df = df.astype({
        "ym"         : str,
        "nation"     : str,
        "industry"   : str,
        "age_level"  : str,
        "trans_count": int,
        "trans_total": int
    })

    return df

#匯出至資料庫
def insert_into_mysql(df: pd.DataFrame, table_name: str = "clean_data"):
    with engine.begin() as conn:
        rows = conn.execute(text(f"SELECT DISTINCT ym, industry, age_level FROM {table_name}")).all()

        existing_keys = {(ym, industry, age_level) for ym, industry, age_level in rows}       
        print(f"[INFO] 資料庫目前已有 year_month： {list(existing_keys)[:5]}")

        df = df.copy()
        df['key']= list(zip(df['ym'], df['industry'], df['age_level']))
        # ~ 在pandas, numpy 是取反
        mask_new = ~df['key'].isin(existing_keys)
        df_new = df.loc[mask_new].drop(columns = ['key'])

        if df_new.empty:
            print("[INFO] 沒有新的資料需要匯入，結束")
            return 
        
        print(f"[INFO] 準備匯入新資料筆數： {len(df_new)}")

    
        df_new.to_sql(
            name = table_name, 
            con = conn, 
            if_exists = "append", 
            index = False, 
            method = "multi", # 一次insert多筆
            chunksize = 1000 # 大筆資料時切塊寫入
        )
        
        print("[INFO] 匯入完成")

def insert_into_mysql_ignore(df: pd.DataFrame, table_name: str = "clean_data", chunksize: int = 1000):
    meta = MetaData()
    table = Table(table_name, meta, autoload_with = engine)

    table_cols = set(c.name for c in table.columns)
    use_cols = [c for c in df.columns if c in table_cols]

    records = df[use_cols].to_dict(orient = "records") 

    if not records:
        print("[INFO] 沒有資料可匯入")
        return 

    with engine.begin() as conn:
        stmt = mysql_insert(table).prefix_with("IGNORE")

        for i in range(0, len(records), chunksize):
            batch = records[i:i + chunksize]
            conn.execute(stmt, batch)
    
    print(f"[INFO] 匯入完成 (重複key) 會自動忽略 {len(records)} 嘗試寫入")

def main():
    print(f"[TIME] {datetime.today()}")
    csv_path = download_csv(OPEN_DATA_CSV_URL, DATA_DIR)
    df = load_and_clean_csv(csv_path)
    insert_into_mysql_ignore(df)
    print("\n")

if __name__ == "__main__":
    t1 = datetime.now()
    main()
    t2 = datetime.now()
    print(f"所需時間 {t2 - t1}")