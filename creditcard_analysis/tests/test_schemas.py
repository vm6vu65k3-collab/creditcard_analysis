import pytest 
from pydantic import ValidationError

from creditcard_analysis.utils.schemas import (
    ChartIn, ChartOut, ChartPoint, ChartType,
    ColumnName, MetricColumn, Filter, ParamsJSON,
    ParamsFigure, TrendPoint, TopIndustry, TopnPerMonth,
    DashboardResponse
)

@pytest.mark.parametrize(
    'enum_item, expected',
    [
        (ColumnName.year_month, 'ym'),
        (ColumnName.industry, 'industry'),
        (ColumnName.age_level, 'age_level')
    ]
)
def test_columnname_enum(enum_item, expected):
    assert enum_item == expected


@pytest.mark.parametrize(
    'enum_item, expected',
    [
        (ChartType.bar, 'bar'),
        (ChartType.line, 'line'),
        (ChartType.pie, 'pie'),
        (ChartType.heatmap, 'heatmap')    
    ]
)
def test_charttype_enum(enum_item, expected):
    assert enum_item == expected


def test_metriccolumn_enum():
    assert MetricColumn.trans_count == 'trans_count'
    assert MetricColumn.trans_total == 'trans_total'


def test_params_json_rejects_same_x_and_y():
    with pytest.raises(ValueError) as e:
        ParamsJSON(
            x_axis = 'industry',
            y_axis = 'industry'
        )
    
    msg = str(e.value)
    assert 'y_axis 不應與 x_axis 相同' in msg

def test_params_json_allow_yaxis_is_none():
    obj = ParamsJSON(x_axis = ColumnName.industry)

    assert obj.y_axis is None 
    assert obj.x_axis == 'industry'


def test_paramsfigure_figsize_allows_list_and_cast_to_tuple():
    obj = ParamsFigure(figsize = [9.0, 7.0])

    assert obj.figsize[0] == 9.0
    assert obj.figsize[1] == 7.0

def test_paramsfigure_figsize_rejects_wrong_length():
    with pytest.raises(ValueError) as e:
        ParamsFigure(figsize = [9.0, 7.0, 8.0])
    
    msg = str(e.value)
    assert 'figsize 長度應為 2 的序列' in msg

def test_paramsfigure_figsize_rejects_negative():
    with pytest.raises(ValueError) as e:
        ParamsFigure(figsize = [0,  8.0])
    
    msg = str(e.value)
    assert 'figsize 需為正數' in msg


def test_chartin_allows_without_yaxis_in_bar(make_chartin):
    obj = make_chartin(
        chart_type = ChartType.bar
    )

    assert obj.params_json.y_axis is None 

def test_chartin_rejects_without_yaxis_in_heatmap(make_chartin):
    with pytest.raises(ValueError) as e:
        obj = make_chartin(
            chart_type = ChartType.heatmap
        )
    msg = str(e.value)

    assert 'heatmap 必須提供 y_axis' in msg 


def test_chartin_ok_with_yaxis_in_heatmap(make_chartin):
    obj = make_chartin(
        chart_type = ChartType.heatmap,
        y_axis = ColumnName.age_level 
    )

    assert obj.params_json.y_axis == 'age_level'


def test_filter_topn_rejects_negative():
    with pytest.raises(ValidationError):
        Filter(topn = -1)

    with pytest.raises(ValidationError):
        Filter(topn = 0)

def test_filter_topn_allows_positive():
    obj = Filter(topn = 5)
    
    assert obj.topn == 5 

def test_filter_allows_none():
    obj = Filter()

    assert obj.industry is None 

def test_chartpoint_reject_without_x():
    with pytest.raises(ValidationError):
        ChartPoint()

def test_chartpoint_allows_y_is_float_str_or_none():
    p1 = ChartPoint(x = 'x', y = 1.5)
    p2 = ChartPoint(x = 'x', y = 'test')
    p3 = ChartPoint(x = 'x')
    
    #方法一
    for s in [1.5, 'test', None]:
        assert isinstance(s, (float, str, type(None)))
    
    #方法二
    assert isinstance(p1.y, float)
    assert isinstance(p2.y, str)
    assert isinstance(p3.y, type(None))

def test_chartout_accepts_points():
    obj = ChartOut(
        key = '202501',
        url = 'https://test.com',
        points = [{'x': 'test', 'amount': 123.1}]
    )

    assert isinstance(obj.points[0].x, str)
    assert isinstance(obj.points[0].amount, float)


def test_dashboard_point_models_ok():
    t = TrendPoint(ym = '202401', amount = 123.1)
    i = TopIndustry(industry = 'food', amount = 666.1)
    m = TopnPerMonth(ym = '202401', industry = 'live', amount = 552.1)

    assert t.ym == '202401'
    assert i.amount == 666.1
    assert m.industry == 'live'

def test_dashboard_accepts_nested_list():
    resp = DashboardResponse(
        trend = [{'ym': '2024', 'amount': 666.1}],
        topn = [{'industry': 'food', 'amount': 111.2}],
        topn_per_month = [{'ym': '202501', 'industry': 'live', 'amount': 777.6}]
    )
    
    assert resp.trend[0].amount == 666.1 
    assert resp.topn[0].industry == 'food'
    assert resp.topn_per_month[0].ym == '202501'