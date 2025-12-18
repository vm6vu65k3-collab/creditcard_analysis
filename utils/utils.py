import pandas as pd 
from typing import Sequence
def get_path(BASE_DIR: str, folder: str, file_name: str):
    path = BASE_DIR / folder / file_name  
    return path  


def handling_missing_value(
    df: pd.DataFrame, 
    num_cols: Sequence[str] | None = None, 
    str_cols: Sequence[str] | None = None
    ) -> pd.DataFrame:
    df = df.copy()

    num_cols = [c for c in (num_cols or []) if c in df.columns]    
    cat_cols = [c for c in (str_cols or []) if c in df.columns]

    for col in num_cols:
        na_ratio = df[col].isna().mean()
        if na_ratio > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            print(f"{col} 欄位缺失率：{na_ratio:.2%} 用中位數{median_val}填補") 
            
    for col in cat_cols:
        na_ratio = df[col].isna().mean()
        if na_ratio == 0:
            continue 

        mode_val = df[col].mode(dropna = True)
        if not mode_val.empty:
            fill_val = mode_val.iloc[0]
            df[col] = df[col].fillna(fill_val) 
            print(f"{col} 欄位缺失率：{na_ratio:.2%} 用眾數填補")
        else:
            print(f"{col} 欄位缺失率：{na_ratio:.2%}，無眾數可填補，保留缺失值")
        
    print("缺失值處理完成")
    return df 

def handling_duplicate_value(df):
    dup_count = df.duplicated().sum()
    if dup_count:
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        print(f"重複值：{dup_count}筆，刪除後筆數：{after}(原本{before})")
    else:
        print("無重複數")
    
    print("重複值處理完成")
    return df

