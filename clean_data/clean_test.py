import requests
import pandas as pd 
from pathlib import Path 
from sqlalchemy import text
from datetime import datetime 
from database import engine
from sqlalchemy.exc import SQLAlchemyError 
from utils import handling_missing_value, handling_duplicate_value

OPEN_DATA_CSV_URL = "https://www.nccc.com.tw/dataDownload/Age%20Group/BANK_TWN_ALL_AG.CSV"

BASE_DIR = Path(__file__).resolve().parent 
DATA_DIR = BASE_DIR / "test_open_data"

def download_data(url: str, save_dir: Path) -> Path:
    save_dir.mkdir(parents = True, exist_ok = True)
    timestamp = datetime.today().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"raw_data{timestamp}.csv"
    
    try:
        with requests.get(url, timeout = (10, 60), verify = False, stream = True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size = 1024*1024):
                    if chunk:
                        f.write(chunk)
    except requests.exceptions.RequestException as e:
        if file_path.exists():
            file_path.unlink()
        raise RuntimeError(f"下載失敗：{e}") from e
    
    print(f"[INFO] CSV 已下載至 {file_path}")
    return file_path


def load_and_clean_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        encoding = "utf-8-sig",
        na_values = ["", " ", "NaN", "Na"]
    )

    columns = ['ym', 'nation', 'industry', 'age_level', 'trans_count', 'trans_total']
    if len(df.columns) != len(columns):
        print(f"[INFO] 欄位數不符，原始欄位數：{len(df.columns)} 預期欄位數：{len(columns)}")
        return

    df.columns = columns
    print(f"欄位標準化：{df.columns.tolist()}")

    num_cols = ['trans_count', 'trans_total']
    str_cols = ['ym', 'nation', 'industry', 'age_level']
    df = handling_missing_value(df, num_cols, str_cols)
    df = handling_duplicate_value(df)

    df = df.astype({
        "ym"         : str,
        "nation"     : str,
        "industry"   : str,
        "age_level"  : str,
        "trans_count": int,
        "trans_total": int
    })

    return df 

def insert_into_sql(df: pd.DataFrame, table_name: str = "clean_data"):
    if df is None or df.empty:
        print("[INFO] df 為空，略過匯入")
        return 
    
    with engine.begin() as conn:
        try:
            rows = conn.execute(text(f"SELECT DISTINCT ym, industry, age_level FROM {table_name}")).all()
            existing_keys = {(ym, industry, age_level) for ym, industry, age_level in rows}
        except SQLAlchemyError as e:
            print(f"[WARN] 查詢既有資料失敗，原因：{e}")
            existing_keys = set()

        df = df.copy()
        df['key'] = list(zip(df['ym'], df['industry'], df['age_level']))
        mask_new = ~df['key'].isin(existing_keys)
        df_new = df.loc[mask_new].drop(columns = ['key'])

        if df_new.empty:
            print("[INFO] 沒有新資料需匯入，結束")
            return 

        print(f"[INFO] 準備匯入資料筆數：{len(df_new)}")

        df_new.to_sql(
            name = table_name,
            con = conn,
            index = False,
            if_exists = 'append',
            method = 'multi',
            chunksize = 1000
        ) 

        print("[INFO] 匯入完成")


def main():
    print(f"[TIME] {datetime.today()}")
    csv_path = download_data(OPEN_DATA_CSV_URL, DATA_DIR)
    df = load_and_clean_csv(csv_path)
    insert_into_sql(df)
    print("\n")

if __name__ == "__main__":
    main()