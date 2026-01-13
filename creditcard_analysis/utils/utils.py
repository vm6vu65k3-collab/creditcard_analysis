import logging
import pandas as pd 
from pathlib import Path
from typing import Sequence

logger = logging.getLogger(__name__)

def get_path(BASE_DIR: Path, folder: str, file_name: str) -> Path:
    return BASE_DIR / folder / file_name    


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
            logger.info("%s 欄位缺失率：%.2f%% 用中位數 %s填補", col, na_ratio * 100, median_val) 
            
    for col in cat_cols:
        na_ratio = df[col].isna().mean()
        if na_ratio == 0:
            continue 

        mode_val = df[col].mode(dropna = True)
        if not mode_val.empty:
            fill_val = mode_val.iloc[0]
            df[col] = df[col].fillna(fill_val) 
            logger.info("%s 欄位缺失率：%.2f%% 用眾數 %s 填補", col, na_ratio * 100, fill_val)
        else:
            logger.info("%s 欄位缺失率：%.2f%%，無眾數可填補，保留缺失值", col, na_ratio * 100)
        
    logger.info("缺失值處理完成")
    return df 

def handling_duplicate_value(df):
    dup_count = df.duplicated().sum()
    if dup_count:
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        logger.info("重複值：%s 筆，刪除後筆數：%s (原本 %s)", dup_count, after, before)
    else:
        logger.info("無重複數")
    
    logger.info("重複值處理完成")
    return df

