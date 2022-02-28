from pydantic import ValidationError
from sanic import exceptions
from sqlalchemy.future import select
from sqlalchemy.sql import func

from app.api.model import CRUDUsersListResponseModel
from app.model.tables import User


async def users_list(di, page, size):
    table = User.__table__

    count_sql = select(func.count(table.c.id))
    id_count = await di.db.val(count_sql)
    len_pages = int(-1 * (id_count / size) // 1 * -1)

    sql = select(table.c.id, table.c.first_name, table.c.last_name, table.c.email)
    users = await di.db.list(sql, page=page, page_size=size)

    try:
        data = CRUDUsersListResponseModel.create(users, len_pages, page, size)
        return data.dict()
    except ValidationError as e:
        print(e.json())
        raise exceptions.SanicException("Validation Error", status_code=422)
