import pytest 
import logging
import pandas as pd
import pandas.testing as pdt 
from pathlib import Path 

from creditcard_analysis.utils.utils import get_path, handling_missing_value, handling_duplicate_value 

# @pytest.fixture
# def caplog_info_utils(caplog):
#     caplog.set_level(logging.INFO, logger = 'creditcard_analysis.utils.utils')
#     return caplog 

# def test_get_path_join():
#     base = Path("/tmp/project")
#     p = get_path(base, 'test1', 'test2')
#     assert p == Path('/tmp/project/test1/test2')


# def test_handling_missing_value_fill_na_with_median(caplog_info_utils):
#     df = pd.DataFrame({'x': [1.0, None, 3.0]})
#     out = handling_missing_value(df, num_cols = ['x'], str_cols = [])
    
#     assert df['x'].isna().sum() == 1

#     expected = pd.DataFrame({'x': [1.0, 2.0, 3.0]})

#     pdt.assert_frame_equal(out, expected)

#     for s in ['用中位數', '缺失值處理完成']:
#         assert s in caplog_info_utils.text

# def test_handling_missing_value_fill_na_with_mode(caplog_info_utils):
#     df = pd.DataFrame({'x': ['a', 'b', 'b', None]})
#     out = handling_missing_value(df, num_cols = [], str_cols = ['x'])
    
#     assert df['x'].isna().sum() == 1
    
#     expected = pd.DataFrame({'x': ['a', 'b', 'b', 'b']})
    
#     pdt.assert_frame_equal(out, expected)
    
#     for s in ['用眾數', '缺失值處理完成']:
#         assert s in caplog_info_utils.text

# def test_handling_missing_value_non_mode_keep_na_value(caplog_info_utils):
#     df = pd.DataFrame({'x': [None, None, None]})
#     out = handling_missing_value(df, str_cols = ['x'], num_cols = [])
    
#     assert df['x'].isna().sum() == 3
    
#     expected = pd.DataFrame({'x': [None, None, None]})
    
#     pdt.assert_frame_equal(out, expected)

#     for s in ['無眾數可填補，保留缺失值', '缺失值處理完成']:
#         assert s in caplog_info_utils.text


# def test_handling_duplicate_value_no_duplicate(caplog_info_utils):
#     df = pd.DataFrame({'x': [1, 2, 3], 'y': ['a', 'b', 'c']})
#     out = handling_duplicate_value(df)

#     assert out.duplicated().sum() == 0
    
#     expected = pd.DataFrame({'x': [1, 2, 3], 'y': ['a', 'b', 'c']})
    
#     pdt.assert_frame_equal(out, expected)

#     for s in ['無重複數', '重複值處理完成']:
#         assert s in caplog_info_utils.text

# def test_handling_duplicate_value_with_duplicate(caplog_info_utils):
#     df = pd.DataFrame({'x': [1, 1, 2], 'y': ['a', 'a', 'b']})
#     out = handling_duplicate_value(df)
#     out2 = out.reset_index(drop = True)
#     assert df.duplicated().sum() == 1

#     expected = pd.DataFrame({'x': [1, 2], 'y': ['a', 'b']})
#     expected2 = expected.reset_index(drop = True)
#     pdt.assert_frame_equal(out2, expected2)

#     for s in ['刪除後筆數', '重複值處理完成']:
#         assert s in caplog_info_utils.text