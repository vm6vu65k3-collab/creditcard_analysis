import pytest
from unittest.mock import MagicMock 

from creditcard_analysis.utils.db_query import get_object_by_id, get_object_by_column 


# def test_get_object_by_id_calls_session_and_return_value():
#     session = MagicMock()
#     model = object()
#     expected = object()
    
#     session.get.return_value = expected 

#     out = get_object_by_id(session, model, 123)

#     assert out is expected 
#     session.get.assert_called_once_with(model, 123)



# def test_get_object_by_column_raise_when_column_missing():
#     session = MagicMock()

#     class DummyModel:
#         __name__ = "DummyModel"
        
    
#     with pytest.raises(AttributeError) as e:
#         get_object_by_column(session, DummyModel, 'foo', 'test')
    
#     assert 'DummyModel 裡沒有 foo 欄位' in str(e.value)

# class Col:
#     def __init__(self, name):
#         self.name = name 
#     def __eq__(self, other):
#         return ('eq', self.name, other)

# class DummyModel:
#     __name__ = "DummyModel"
#     id = Col("id")
#     name = Col("name")


# def test_get_object_by_column_calls_session_filter_first_and_return():
#     session = MagicMock()

#     query = MagicMock()
#     session.query.return_value = query 

#     expected = object()
#     query.filter.return_value.first.return_value = expected 

#     out = get_object_by_column(session, DummyModel, 'name', 'Bruce')
    
#     assert out is expected 
    
#     session.query.assert_called_once_with(DummyModel)
#     query.filter.assert_called_once_with(('eq', 'name', 'Bruce'))
#     query.filter.return_value.first.assert_called_once_with()