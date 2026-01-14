import pytest 
import logging 
from pydantic import ValidationError


from creditcard_analysis.utils.schemas import (
    ChartPoint, ChartIn, ChartOut, ChartType,
    ColumnName, MetricColumn, Filter,
    ParamsJSON, ParamsFigure, TrendPoint, 
    TopIndustry, TopnPerMonth, DashboardResponse
    
)
#====================== ColumnName ====================== 

# @pytest.mark.parametrize(
#     "enum_item, expected",
#     [
#         (ColumnName.year_month, 'ym'),
#         (ColumnName.industry, 'industry'),
#         (ColumnName.age_level, 'age_level')
#     ]
# )
# def test_columnname_values(enum_item, expected):
#     assert enum_item.value == expected


#====================== ChartType ====================== 

# @pytest.mark.parametrize(
#     "enum_item, expected",
#     [
#         (ChartType.bar, 'bar'),
#         (ChartType.line, 'line'),
#         (ChartType.pie, 'pie'),
#         (ChartType.heatmap, 'heatmap')
#     ]
# )
# def test_charttype_value(enum_item, expected):
#     assert enum_item.value == expected


#====================== MetricColumn ====================== 

# def test_MetricColumn():
#     assert MetricColumn.trans_count == 'trans_count'
#     assert MetricColumn.trans_total == 'trans_total'

#====================== ParamsJSON ====================== 

# def test_paramsjson_ok_when_yaxis_is_none():
#     obj = ParamsJSON(x_axis = ColumnName.industry)
#     assert obj.x_axis == ColumnName.industry
#     assert obj.y_axis is None 

# def test_paramsjson_reject_same_x_and_y():
#     with pytest.raises(ValidationError) as e:
#         ParamsJSON(x_axis = ColumnName.industry, y_axis = ColumnName.industry)
    
#     msg = str(e.value)
#     assert "y_axis 不應與 x_axis 相同" in msg

#====================== ParamsFigure ====================== 

# def test_paramsfigure_figsize_accept_list_and_cast_to_tuple():
#     fig = ParamsFigure(figsize = [10, 8])
#     assert fig.figsize == (10.0, 8.0)

# def test_paramsfigure_figsize_reject_wrong_length():
#     with pytest.raises(ValidationError) as e:
#         ParamsFigure(figsize = [10, 8, 6])
#     assert "figsize 長度應為 2 的序列" in str(e.value)

# def test_paramsfigure_reject_non_positive():
#     with pytest.raises(ValidationError) as e:
#         ParamsFigure(figsize = [0, 8])
    
#     msg = str(e.value)
#     assert 'figsize 需為正數' in msg


#====================== ChartIn ====================== 

# def test_chartin_bar_allows_missing_yaxis(make_chartin):
#     obj = make_chartin(ChartType.bar, x_axis = ColumnName.industry)
#     assert obj.chart_type == ChartType.bar 
#     assert obj.params_json.y_axis is None

# def test_chartin_heatmap_not_allows_missing_yaxis(make_chartin):
#     with pytest.raises(ValidationError) as e:
#         obj = make_chartin(ChartType.heatmap, x_axis = ColumnName.industry)
#         assert obj.chart_type == ChartType.heatmap 
        
#     msg = str(e.value)
#     assert 'heatmap 必須提供 y_axis' in msg 

# def test_chartin_heatmap_ok_with_yaxis(make_chartin):
#     obj = make_chartin(ChartType.heatmap, x_axis = ColumnName.industry, y_axis = ColumnName.age_level)
#     assert obj.chart_type == ChartType.heatmap 
#     assert obj.params_json.y_axis == ColumnName.age_level

#====================== Filter ====================== 

# def test_filter_topn_allows_none():
#     f = Filter()
#     assert f.topn is None 

# def test_filter_topn_allows_positive():
#     f = Filter(topn = 30)
#     assert f.topn == 30

# def test_filter_topn_not_allows_negative():
#     with pytest.raises(ValidationError):
#         Filter(topn = 0)
    
#     with pytest.raises(ValidationError):
#         Filter(topn = -5)

#====================== ChartPoint ====================== 

# def test_chartpoint_y_accepts_str_or_float_or_none():
#     p1 = ChartPoint(x = '202401', y = 'A')
#     p2 = ChartPoint(x = '202401', y = 1.1)
#     p3 = ChartPoint(x = '202401', y = None)
#     assert p1.y == 'A'
#     assert p2.y == 1.1 
#     assert p3.y is None 

#====================== ChartOut ====================== 

# def test_chartout_accepts_points():
#     out = ChartOut(
#         key = 'abc',
#         url = "http://test.com",
#         points = [{"x": "202401", "amount": 123.0}]
#     )

#     assert out.key == 'abc'
#     assert out.url == "http://test.com"
#     assert out.points[0].x == '202401'
#     assert out.points[0].amount == 123.0

# def test_chartout_rejects_invalid_points():
#     with pytest.raises(ValidationError):
#         ChartOut(ke = 'abc', points = [{'x': 123}])

# def test_dashboard_points_models_ok():
#     t = TrendPoint(ym = '202401', amount = 12.3)
#     i = TopIndustry(industry = '食', amount = 24.1)
#     m = TopnPerMonth(ym = '202401', industry = '住', amount = 60.1)

#     assert t.ym == '202401'
#     assert i.industry == '食'
#     assert m.amount == 60.1

# def test_dashboardresponse_accept_nested_list():
#     resp = DashboardResponse(
#         trend = [{'ym': '202401', 'amount': 123.1}],
#         topn = [{'industry': '衣', 'amount': 122.1}],
#         topn_per_month = [{'ym': '202412', 'industry': '其他', 'amount': 166.7}]
#     )

#     assert resp.trend[0].ym  == '202401'
#     assert resp.topn[0].amount == 122.1
#     assert resp.topn_per_month[0].industry == '其他'

# def test_dashbaordresponse_rejects_missing_fields():
#     with pytest.raises(ValidationError):
#         DashboardResponse(
#             trend = [],
#             topn = [],

#         )