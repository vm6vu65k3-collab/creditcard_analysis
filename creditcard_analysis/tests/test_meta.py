import pytest 
from pydantic import ValidationError
from creditcard_analysis.utils.meta import Option, MetaPayload 

# def test_option_typing():
#     obj = Option(
#         key = 'abc',
#         value = 'xyz'
#     )

#     assert obj.key == 'abc'
#     assert obj.value == 'xyz'

# def test_option_reject_non_string():
#     with pytest.raises(ValidationError):
#         Option(key = 123, value = 'x')


# def test_metapayload_columns():
#     obj = MetaPayload(
#         columns = [{"key": "test", "value": "123"}],
#         chart_type = [{"key": "abc", "value": "222"}]
#     )

#     assert obj.columns[0].key == 'test'
#     assert obj.chart_type[0].value == '222'