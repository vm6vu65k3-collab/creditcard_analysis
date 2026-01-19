import pytest
from typing import get_origin, get_args, Annotated 
from fastapi.params import Depends as DependsClass

from creditcard_analysis.utils import deps 

# class FakeDB:
#     def __init__(self):
#         self.closed = False 
#     def close(self):
#         self.closed = True 


# def test_get_db_yield_session_and_close(monkeypatch):
#     fake = FakeDB()

#     def fake_sessionlocal():
#         return fake 
    
#     monkeypatch.setattr(deps, 'SessionLocal', fake_sessionlocal)

#     gen = deps.get_db()
#     db = next(gen)

#     assert db is fake 
#     assert fake.closed is False 

#     gen.close()
#     assert fake.closed is True 


# def test_get_db_close_even_when_exception(monkeypatch):
#     fake = FakeDB()
    
#     def fake_sessionlocal():
#         return fake 
    
#     monkeypatch.setattr(deps, 'SessionLocal', fake_sessionlocal)
    
#     gen = deps.get_db()
#     _ = next(gen)

#     with pytest.raises(RuntimeError):
#         gen.throw(RuntimeError('boom'))
    
#     assert fake.closed is True


# def test_db_annotated_points_to_get_db():
#     origin = get_origin(deps.Db)
#     assert origin is Annotated 

#     args = get_args(deps.Db)
#     assert len(args) >= 2 

#     session_type = args[0]
#     metadata = args[1:]

#     assert session_type is deps.Session 
    
#     depends_obj = next((m for m in metadata if isinstance(m, DependsClass)), None)
#     assert depends_obj is not None 
#     assert depends_obj.dependency is deps.get_db