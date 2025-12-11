

def get_object_by_id(session, model, model_id: int ):
    return session.get(model, model_id)

def get_object_by_column(session, model, column_name: str, value):
    if not hasattr(model, column_name):
        raise AttributeError(f"{model.__name__} 裡沒有 {column_name} 欄位")
    return session.query(model).filter(getattr(model, column_name) == value).first()