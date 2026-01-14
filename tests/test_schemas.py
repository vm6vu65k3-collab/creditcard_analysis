import pytest 
from pydantic import ValidationError

from creditcard_analysis.utils.schemas import (
    ChartPoint, ChartType, ChartIn, ChartOut,
    ColumnName, MetricColumn, Filter, ParamsJSON,
    ParamsFigure,  TrendPoint, TopIndustry, TopnPerMonth,
    DashboardResponse
)

# @pytest.mark.parametrize(
#         "enum_item, expected",
#         [
#             (ColumnName.year_month, 'ym'),
#             (ColumnName.industry, 'industry'),
#             (ColumnName.age_level, 'age_level')
#         ]
# )
# def test_columnname_enum(enum_item, expected):
#     assert enum_item == expected

# @pytest.mark.parametrize(
#     "enum_item, expected",
#     [
#         (ChartType.bar, 'bar'),
#         (ChartType.line, 'line'),
#         (ChartType.pie, 'pie'),
#         (ChartType.heatmap, 'heatmap')
#     ]
# )
# def test_charttype_enum(enum_item, expected):
#     assert enum_item == expected


# def test_metriccolumn_enum():
#     assert MetricColumn.trans_count == 'trans_count'
#     assert MetricColumn.trans_total == 'trans_total'

# def test_paramsjson_rejects_same_x_y():
#     with pytest.raises(ValidationError) as e:
#         ParamsJSON(
#             x_axis = ColumnName.industry,
#             y_axis = ColumnName.industry
#         )
        
#     msg = str(e.value)
#     assert 'y_axis 不應與 x_axis 相同' in msg


# def test_paramsjson_allow_yaxis_is_none():
#     obj = ParamsJSON(x_axis = ColumnName.industry)

#     assert obj.x_axis == 'industry'
#     assert obj.y_axis is None 

# def test_paramsfigure_figsize_allow_list_and_cast_to_tuple():
#     obj = ParamsFigure(figsize = [11.0, 12.0])

#     assert obj.figsize[0] == 11.0
#     assert obj.figsize[1] == 12.0

# def test_paramsfigure_figsize_rejects_wrong_length():
#     with pytest.raises(ValidationError) as e:
#         ParamsFigure(figsize = [12.0, 11.0, 13.0])
        
#     msg = str(e.value)
#     assert 'figsize 長度應為 2 的序列' in msg

# def test_paramsfigure_figsize_rejescts_negative():
#     with pytest.raises(ValidationError) as e:
#         ParamsFigure(figsize = [0, 12])
#     msg = str(e.value)
#     assert 'figsize 需為正數' in msg

# def test_chartin_allows_without_y_axis_in_bar(make_chartin):
#     obj = make_chartin(
#         chart_type = ChartType.bar
#     )

#     assert obj.params_json.y_axis is None 

# def test_chartin_reject_without_y_axis_in_heatmap(make_chartin):
#     with pytest.raises(ValidationError) as e:
#         make_chartin(
#             chart_type = ChartType.heatmap
#         )
#     msg = str(e.value)
#     assert 'heatmap 必須提供 y_axis' in msg

# def test_chartin_ok_with_y_axis_in_heatmap(make_chartin):
#     obj = make_chartin(
#         chart_type = ChartType.heatmap,
#         y_axis = ColumnName.age_level
#     )

#     assert obj.params_json.y_axis == 'age_level'

# def test_filter_topn_reject_negative():
#     with pytest.raises(ValidationError):
#         Filter(topn = -5)
        
#     with pytest.raises(ValidationError):
#         Filter(topn = 0)

# def test_filter_topn_allows_positive():
#     obj = Filter(topn = 5)
#     assert obj.topn == 5

# def test_filter_topn_allows_none():
#     obj = Filter()
#     assert obj.topn is None

# def test_chartpoint_y_accepts_float_str_none():
#     p1 = ChartPoint(x = '202401', y = 'a')
#     p2 = ChartPoint(x = '202402', y = 123.1)
#     p3 = ChartPoint(x = '202403')

#     assert p1.y == 'a'
#     assert p2.y == 123.1
#     assert p3.y is None

# def test_chartout_accepts_points():
#     obj = ChartOut(
#         key = 'abc',
#         url = 'https://test.com',
#         points = [{'x': 'a', 'amount': 123.1}]
#     )

#     assert obj.key == 'abc'
#     assert obj.url == 'https://test.com'
#     assert obj.points[0].x == 'a'
#     assert obj.points[0].amount == 123.1 