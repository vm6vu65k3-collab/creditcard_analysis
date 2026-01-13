import logging
import pandas as pd 
import pandas.testing as pdt 
from pathlib import Path 
from creditcard_analysis.utils.utils import get_path, handling_missing_value, handling_duplicate_value

def test_get_path_join():
    base = Path("/tmp/project")
    p = get_path(base, "data", "a.csv")
    assert p == Path("/tmp/project/data/a.csv")


def test_handling_missing_value_fill_numeric_with_median(caplog):
    caplog.set_level(logging.INFO, logger = 'creditcard_analysis.utils.utils')

    df = pd.DataFrame({"x": [1.0, None, 3.0]})
    out = handling_missing_value(df, num_cols = ['x'], str_cols = [])
    
    assert df['x'].isna().sum() == 1

    expect = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
    pdt.assert_frame_equal(out, expect)

    assert "缺失值處理完成" in caplog.text


# def test_handling_missing_value_fill_category_with_mode(capsys):
#     df = pd.DataFrame({"cat": ['A', None, 'A', 'B']})
#     out = handling_missing_value(df, num_cols = [], str_cols = ['cat'])
    
#     expect = pd.DataFrame({"cat": ['A', 'A', 'A', 'B']})
#     pdt.assert_frame_equal(out, expect)
    
#     captured = capsys.readouterr().out
#     assert "cat 欄位缺失率" in captured 
#     assert "缺失值處理完成" in captured

# def test_handling_missing_value_category_mode_empty_keep_na(capsys):
#     df = pd.DataFrame({"cat": [None, None, None, None]})
#     out = handling_missing_value(df, num_cols = [], str_cols = ['cat'])
    
#     assert out['cat'].isna().all()
    
#     captured = capsys.readouterr().out 
#     assert "無眾數可填補，保留缺失值" in captured 
#     assert "缺失值處理完成" in captured

# def test_handling_missing_value_ignore_unknown_columns(caplog):
#     df = pd.DataFrame({"x": [1.0, None, 3.0]})

#     out = handling_missing_value(df, num_cols = ['x', 'y'], str_cols = ['cat'])
    
#     assert out['x'].isna().sum() == 0
#     assert "缺失值處理完成" in caplog.text
# def test_handling_duplicate_value_drop_duplicartes(capsys):
#     df = pd.DataFrame({"a": [1, 1, 2], "b": ['x', 'x', 'y']})

#     out = handling_duplicate_value(df)
#     expect = pd.DataFrame({"a": [1, 2], "b": ['x', 'y']})
#     expect = expect.reset_index(drop = True)
#     out2 = out.reset_index(drop = True)
    
#     pdt.assert_frame_equal(out2, expect)

#     captured = capsys.readouterr().out
#     assert "重複值處理完成" in captured


# def test_handling_duplicate_value_no_duplicates(capsys):
#     df = pd.DataFrame({"a": [1, 2, 3], "b": ['x', 'y', 'z']})
    
#     out = handling_duplicate_value(df)
    
#     pdt.assert_frame_equal(out.reset_index(drop = True), df.reset_index(drop = True))
    
#     captured = capsys.readouterr().out
#     assert "無重複數" in captured
    