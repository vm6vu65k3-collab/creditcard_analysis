import requests, urllib3
import pandas as pd 
from pathlib import Path
from datetime import datetime 
from sqlalchemy import text
from ..utils import handling_missing_value, handling_duplicate_value
from ..database import engine

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OPEN_DATA_CSV_URL = "https://www.nccc.com.tw/dataDownload/Age%20Group/BANK_TWN_ALL_AG.CSV"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "open_data_downloads"

def download_csv(url: str, save_dir: Path) -> Path:
    save_dir.mkdir(parents = True, exist_ok = True)
    
    today = datetime.today().strftime("%Y%m%d")
    file_path = save_dir / f"raw_open_data{today}.csv"

    resp = requests.get(url, timeout = 60, verify = False)
    resp.raise_for_status()

    file_path.write_bytes(resp.content)
    print(f"[INFO] CSV 已下載到：{file_path}")
    return file_path

def load_and_clean_csv(csv_path: Path) -> pd.DataFrame:
    
    df = pd.read_csv(
        csv_path,
        encoding = "utf-8-sig",
        na_values = ["", " ", "Na", "NaN"]
    )

    #標準化欄位處理
    columns = ['ym', 'nation', 'industry', 'age_level', 'trans_count', 'trans_total']
    if len(df.columns) != len(columns):
        print(f"欄位數不符，原始欄位數{len(df.columns)} 預期欄位{len(columns)}")

    df.columns = columns
    print("標準化欄位", df.columns.tolist())

    #缺失及重複值處理
    num_cols = ['trans_count', 'trans_total']
    str_cols = ['ym', 'nation', 'industry', 'age_level']
    df = handling_missing_value(df, num_cols = num_cols, cat_cols = str_cols)
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
        rows = conn.execute(text("SELECT DISTINCT ym, industry, age_level FROM clean_data")).all()

        existing_keys = {(ym, industry, age_level) for ym, industry, age_level in rows}       
        print(f"[INFO] 資料庫目前已有 year_month： {list(existing_keys)[:5]}")

        df = df.copy()
        df['key']= list(zip(df['ym'], df['industry'], df['age_level']))

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

def main():
    print(f"[TIME]{datetime.today()}")
    csv_path = download_csv(OPEN_DATA_CSV_URL, DATA_DIR)
    df = load_and_clean_csv(csv_path)
    insert_into_mysql(df)
    print("\n")

if __name__ == "__main__":
    main()
