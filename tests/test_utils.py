import logging
import pytest
import pandas as pd 
import pandas.testing as pdt 
from pathlib import Path 
from creditcard_analysis.utils.utils import get_path, handling_missing_value, handling_duplicate_value

@pytest.fixture
def caplog_info_utils(caplog):
    caplog.set_level(logging.INFO, logger = 'cerditcard_analysis.utils.utils')
    return caplog

# def test_get_path_join():
#     bash = Path("/tmp/project")
#     p = get_path(bash, 'test', 'test_data.csv')
#     assert p == Path("/tmp/project/test/test_data.csv")


# def test_handling_missing_value_fill_numeric_with_median(caplog_info_utils): 
#     df = pd.DataFrame({"x": [1.0, 2.0, 5.0, None]})
#     out = handling_missing_value(df, num_cols = ['x'], str_cols = [])

#     assert df['x'].isna().sum() == 1

#     expect = pd.DataFrame({"x": [1.0, 2.0, 5.0, 2.0]})
#     pdt.assert_frame_equal(out, expect)

#     for s in ['x 欄位缺失率', '缺失值處理完成']:
#         assert s in caplog_info_utils.text


# def test_handling_value_fill_string_with_mode(caplog_info_utils):
#     df = pd.DataFrame({"x": ['a', 'b', 'b', None]})
#     out = handling_missing_value(df, num_cols = [], str_cols = ['x'])
    
#     assert df['x'].isna().sum() == 1

#     expect = pd.DataFrame({'x': ['a', 'b', 'b', 'b']})
#     pdt.assert_frame_equal(out, expect)
    
#     for s in ['x 欄位缺失率', '缺失值處理完成']:
#         assert s in caplog_info_utils.text


def test_handling_value_category_mode_empty_keep_na(caplog_info_utils):
    df = pd.DataFrame({"x": [None, None, None]})
    out = handling_missing_value(df, num_cols = [], str_cols = ['x'])
    
    assert df['x'].isna().sum() == 3

    expect = pd.DataFrame({"x": [None, None, None]})
    pdt.assert_frame_equal(out, expect)

    for s in ['保留缺失值', '缺失值處理完成']:
        assert s in caplog_info_utils.text