from sanic import exceptions
from sqlalchemy.future import select

from app.model.tables import User


async def check_admin(di, login):
    sql = select(User.__table__.c.is_admin).where(User.email == login)
    admin_check = await di.db.val(sql)
    if not admin_check:
        raise exceptions.Forbidden("Response 403 Private Users Private Users Get")
