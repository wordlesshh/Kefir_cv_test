from functools import wraps
from inspect import isawaitable

from sanic import exceptions
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.abs import IDi


def error_handling(fn):
    @wraps(fn)
    async def inner(*args, **kwargs):
        try:
            retval = fn(*args, **kwargs)
            if isawaitable(retval):
                retval = await retval
            return retval
        except IntegrityError as e:
            e = str(e)
            if 'UniqueViolation' in e and 'email' in e:
                raise exceptions.Forbidden('email already exists')
            elif 'ForeignKeyViolation' in e and 'city' in e:
                raise exceptions.Forbidden("city_id doesn't exist")
            raise exceptions.Forbidden("db exception")
    return inner


class Db(IDi):

    Base = declarative_base()

    def __init__(self, di, db_url=None) -> None:
        super().__init__(di)
        self._db_url = self.build_connection_string() if db_url is None else db_url
        self.__engine = create_async_engine(self._db_url, echo=True)
        self.__session = sessionmaker(self.__engine, expire_on_commit=False, class_=AsyncSession)

    def build_connection_string(self):
        return '{}://{}:{}@{}:{}/{}'.format(
            self._di.config['db']['scheme'],
            self._di.config['db']['username'],
            self._di.config['db']['password'],
            self._di.config['db']['host'],
            self._di.config['db']['port'],
            self._di.config['db']['db_name'],
        )

    @error_handling
    async def db_start(self, sql, first_admin):
        async with self.__engine.begin() as conn:
            await conn.run_sync(self.Base.metadata.create_all)
        admin_check = await self.val(sql)
        if not admin_check:
            await self.add_user(first_admin)
        await self.__engine.dispose()

    @error_handling
    async def exec(self, sql, data=None):
        try:
            response = await self.__execute_query(sql, data)
            if response.is_insert:
                result = response.inserted_primary_key[0]
            else:
                result = None
        except IntegrityError as e:
            print(e)
            result = None
        finally:
            await self.__engine.dispose()

        return result

    @error_handling
    async def __execute_query(self, sql, data=None, page=0, page_size=None):
        if data is None:
            data = {}
        try:
            async with self.__session() as session:
                async with session.begin():
                    if page:
                        start = (page - 1) * page_size
                        sql = sql.limit(page_size).offset(start)
                        result = await session.execute(sql, data)
                        return result
                    result = await session.execute(sql, data)
        except OperationalError as e:
            print(e)

        return result

    @error_handling
    async def add_user(self, user):
        from app.model.tables import User

        async with self.__session() as session:
            async with session.begin():
                sql = select(User.__table__.c.email).where(User.email == user.email)
                user_check = await self.val(sql)
                if not user_check:
                    session.add(user)
                    return user
                await session.commit()

        await self.__engine.dispose()

    @error_handling
    async def val(self, sql, data=None):
        rows = await self.__execute_query(sql, data=data)
        row = rows.fetchone()
        if row is None:
            return None
        result = row[0]
        await self.__engine.dispose()
        return result

    @error_handling
    async def row(self, sql, data=None):
        rows = await self.__execute_query(sql, data=data)
        row = rows.fetchone()
        if row is None:
            await self.__engine.dispose()
            return None
        result = {column: value for column, value in row._mapping.items()}
        await self.__engine.dispose()
        return result

    @error_handling
    async def list(self, sql, data=None, page=0, page_size=None):
        rows = await self.__execute_query(
            sql, data=data, page=page, page_size=page_size
        )
        result = [row._mapping.items() for row in rows]
        await self.__engine.dispose()
        return result

    @error_handling
    async def update(self, sql, data):
        response = await self.__execute_query(sql, data=data)
        if response.is_insert:
            result = response.inserted_primary_key
        else:
            result = response.context.compiled_parameters
        await self.__engine.dispose()
        return result
