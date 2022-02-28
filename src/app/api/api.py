import json as json_

from pydantic import ValidationError
from sanic import exceptions
from sanic.blueprints import Blueprint
from sanic.response import empty, json, text
from sanic_ext import openapi, validate
from sqlalchemy.future import select
from sqlalchemy.sql import delete
from sqlalchemy.sql import text as text_
from sqlalchemy.sql import update
from werkzeug.security import check_password_hash, generate_password_hash

from app.helpers import (check_admin, find_date, json_serial,
                         request_validation, users_list)
from app.model.tables import City, User

from .cookies import create_token, verify_token
from .model import (CRUDPrivateUsersListResponseModel,
                    CurrentUserResponseModel, ErrorResponseModel,
                    HTTPValidationError, LoginModel, PrivateCreateUserModel,
                    PrivateDetailUserResponseModel, PrivateUpdateUserModel,
                    PrivateUsersListResponseModel, UpdateUserModel,
                    UpdateUserResponseModel, UsersListResponseModel)


def auth_api(di):
    auth = Blueprint('auth')

    @auth.post('/login')
    @openapi.tag("auth")
    @openapi.summary("Вход в систему")
    @openapi.description("После успешного входа в систему устанавливаются Cookies для пользователя")
    @openapi.response(200, {"application/json": CurrentUserResponseModel}, description='Successful Response')
    @openapi.response(400, {"application/json": ErrorResponseModel}, description='Bad Request')
    @openapi.response(422, {"application/json": HTTPValidationError}, description='Validation Error')
    @openapi.body({"application/json": LoginModel}, required=True)
    @validate(json=LoginModel)
    @request_validation()
    async def login_login_post(request, body: LoginModel):
        sql = select(User.__table__).where(User.email == body.login)
        is_user = await di.db.row(sql)

        if is_user and check_password_hash(is_user['password_hash'], body.password):
            [is_user.pop(key) for key in ['id', 'password_hash', 'additional_info', 'city']]
            response_user = CurrentUserResponseModel(**is_user)
            token = create_token(di, body.login)
            ser_data = json_.dumps(response_user.dict(), default=json_serial)
            ser_data = json_.loads(ser_data)
            response_ = json(ser_data)
            response_.cookies['token'] = token
            return response_
        else:
            raise exceptions.SanicException("Validation Error", status_code=422)

    @auth.get('/logout')
    @openapi.tag("auth")
    @openapi.summary("Выход из системы")
    @openapi.description("При успешном выходе удаляются установленные Cookies")
    @openapi.response(200, {"application/json": None}, description='Successful Response')
    async def logout_logout_get(request):
        response_ = empty(200)
        del response_.cookies['token']
        return response_

    return auth


def user_api(di):
    user = Blueprint('user', url_prefix='/users')

    @user.get('/current')
    @openapi.tag("user")
    @openapi.summary("Получение данных о текущем пользователе")
    @openapi.description("Здесь находится вся информация, доступная пользователю о самом себе, а так же информация "
                         "является ли он администратором")
    @openapi.response(200, {"application/json": CurrentUserResponseModel}, description='Successful Response')
    @openapi.response(400, {"application/json": ErrorResponseModel}, description='Bad Request')
    @openapi.response(401, {"application/json": 'Response 401 Current User Users Current Get'})
    @request_validation(check_token=True)
    async def current_user_users_current_get(request):
        login_by_token = verify_token(di, request.cookies.get("token"))
        table = User.__table__
        sql = select(
            table.c.first_name,
            table.c.last_name,
            table.c.email,
            table.c.is_admin,
            table.c.other_name,
            table.c.phone,
            table.c.birthday
        ).where(User.email == login_by_token)
        user_ = await di.db.row(sql)

        if user_:
            user__ = CurrentUserResponseModel(**user_)
            ser_data = json_.dumps(user__.dict(), default=json_serial)
            data = json_.loads(ser_data)
            response_ = json(data)
            return response_
        else:
            raise exceptions.Unauthorized("Response 401 Current User Users Current Get")

    @user.get('/')
    @openapi.tag("user")
    @openapi.summary("Постраничное получение кратких данных обо всех пользователях")
    @openapi.description("Здесь находится вся информация, доступная пользователю о других пользователях")
    @openapi.response(200, {"application/json": UsersListResponseModel}, description='Successful Response')
    @openapi.response(400, {"application/json": ErrorResponseModel}, description='Bad Request')
    @openapi.response(401, {"application/json": 'Response 401 Current User Users Current Get'})
    @openapi.response(422, {"application/json": HTTPValidationError}, description='Validation Error')
    @openapi.parameter("Page", int, location="header", required=True)
    @openapi.parameter("Size", int, location="header", required=True)
    @request_validation(pagination=True, check_token=True)
    async def users_users_get(request):
        page = int(request.headers.get('Page', None))
        size = int(request.headers.get('Size', None))
        verify_token(di, request.cookies.get("token"))
        response_ = json(await users_list(di, page, size))
        return response_

    @user.patch('/<pk>', strict_slashes=True)
    @openapi.tag("user")
    @openapi.summary("Изменение данных пользователя")
    @openapi.description("Здесь пользователь имеет возможность изменить свои данные")
    @openapi.response(200, {"application/json": UpdateUserResponseModel}, description='Successful Response')
    @openapi.response(400, {"application/json": ErrorResponseModel}, description='Bad Request')
    @openapi.response(401, {"application/json": 'Response 401 Edit User Users  Pk  Patch'})
    @openapi.response(404, {"application/json": 'Response 404 Edit User Users  Pk  Patch'})
    @openapi.response(422, {"application/json": HTTPValidationError}, description='Validation Error')
    @openapi.parameter("pk", int, location="query")
    @openapi.body({"application/json": UpdateUserModel}, required=True)
    @validate(json=UpdateUserModel)
    @request_validation(check_token=True, check_pk=True)
    async def edit_user_users__pk__patch(request, pk, body: UpdateUserModel):
        pk = int(pk)
        login_by_token = verify_token(di, request.cookies.get("token"))

        sql = select(User.__table__).where(User.email == login_by_token)
        user_by_login = await di.db.row(sql)
        sql = select(User.__table__.c.id).where(User.id == pk)
        user_by_pk = await di.db.row(sql)

        if not user_by_login:
            raise exceptions.Unauthorized("Response 401 Current User Users Current Get")
        if not user_by_pk:
            raise exceptions.NotFound('Response 404 Edit User Users  Pk  Patch')
        if user_by_login('id') != user_by_pk['id']:
            raise exceptions.Unauthorized("Response 401 Current User Users Current Get")

        body = body.dict()
        body['id'] = pk
        body['birthday'] = find_date(body['birthday'])
        try:
            UpdateUserResponseModel(**body)
        except ValidationError as e:
            print(e.json())
            raise exceptions.SanicException("Validation Error", status_code=422)

        sql = text_('''
            UPDATE users SET 
            first_name = :first_name,
            last_name = :last_name,
            email = :email,
            other_name = :other_name,
            phone = :phone,
            birthday = :birthday
            WHERE
            id = :id
        ''')
        user_ = await di.db.update(sql, body)
        ser_data = json_.dumps(user_, default=json_serial)
        data = json_.loads(ser_data)
        response_ = json(data)
        return response_

    return user


def private_user_api(di):
    private_user = Blueprint('admin', url_prefix='/private/users')

    @private_user.get('/')
    @openapi.tag("admin")
    @openapi.summary("Постраничное получение кратких данных обо всех пользователях")
    @openapi.description("Здесь находится вся информация, доступная пользователю о других пользователях")
    @openapi.response(200, {"application/json": PrivateUsersListResponseModel}, description='Successful Response')
    @openapi.response(400, {"application/json": ErrorResponseModel}, description='Bad Request')
    @openapi.response(401, {"application/json": 'Response 401 Private Users Private Users Get'})
    @openapi.response(403, {"application/json": 'Response 403 Private Users Private Users Get'})
    @openapi.response(422, {"application/json": HTTPValidationError}, description='Validation Error')
    @openapi.parameter("Page", int, location="header", required=True)
    @openapi.parameter("Size", int, location="header", required=True)
    @request_validation(pagination=True, check_token=True)
    async def private_users_private_users_get(request):
        page = int(request.headers.get('Page', None))
        size = int(request.headers.get('Size', None))
        login_by_token = verify_token(di, request.cookies.get("token"))
        await check_admin(di, login_by_token)

        users_list_ = await users_list(di, page, size)
        sql = select(City.__table__)
        cities_list = await di.db.list(sql)
        len_pages = users_list_['meta']['pagination']['total']
        data = CRUDPrivateUsersListResponseModel.create(users_list_['data'], page, size, len_pages, cities_list)
        response_ = json(data.dict())
        return response_

    @private_user.post('/')
    @openapi.tag("admin")
    @openapi.summary("Создание пользователя")
    @openapi.description("Здесь возможно занести в базу нового пользователя с минимальной информацией о нем")
    @openapi.response(201, {"application/json": PrivateDetailUserResponseModel}, description='Successful Response')
    @openapi.response(400, {"application/json": ErrorResponseModel}, description='Bad Request')
    @openapi.response(401, {"application/json": 'Response 401 Private Users Private Users Get'})
    @openapi.response(403, {"application/json": 'Response 403 Private Users Private Users Get'})
    @openapi.response(422, {"application/json": HTTPValidationError}, description='Validation Error')
    @openapi.body({"application/json": PrivateCreateUserModel}, required=True)
    @validate(json=PrivateCreateUserModel)
    @request_validation(pagination=False, check_token=True)
    async def private_create_users_private_users_post(request, body: PrivateCreateUserModel):
        login_by_token = verify_token(di, request.cookies.get("token"))
        await check_admin(di, login_by_token)

        body = body.dict()
        body['password_hash'] = generate_password_hash(body.pop('password'))
        sql = User.__table__.insert()
        added_user_id = await di.db.exec(sql, body)
        if not added_user_id:
            raise exceptions.Forbidden("Response 403 Private Users Private Users Get")
        body.pop('password_hash')
        body['id'] = added_user_id
        ser_data = json_.dumps(body, default=json_serial)
        data = json_.loads(ser_data)
        added_user = PrivateDetailUserResponseModel(**data)
        response_ = json(added_user.dict(), status=201)
        return response_

    @private_user.get('/<pk>', strict_slashes=True)
    @openapi.tag("admin")
    @openapi.summary("Детальное получение информации о пользователе")
    @openapi.description("Здесь администратор может увидеть всю существующую пользовательскую информацию")
    @openapi.response(200, {"application/json": PrivateDetailUserResponseModel}, description='Successful Response')
    @openapi.response(400, {"application/json": ErrorResponseModel}, description='Bad Request')
    @openapi.response(401, {"application/json": 'Response 401 Private Users Private Users Get'})
    @openapi.response(403, {"application/json": 'Response 403 Private Users Private Users Get'})
    @openapi.response(422, {"application/json": HTTPValidationError}, description='Validation Error')
    @openapi.parameter("pk", int, location="query")
    @request_validation(pagination=False, check_token=True, check_pk=True)
    async def private_get_user_private_users__pk__get(request, pk):
        pk = int(pk)
        login_by_token = verify_token(di, request.cookies.get("token"))
        await check_admin(di, login_by_token)

        sql = select(User.__table__).where(User.id == pk)
        request_user = await di.db.row(sql)
        if not request_user:
            raise exceptions.Forbidden("Response 403 Private Users Private Users Get")
        request_user.pop('password_hash')
        added_user = PrivateDetailUserResponseModel(**request_user)
        ser_data = json_.dumps(added_user.dict(), default=json_serial)
        data = json_.loads(ser_data)
        response_ = json(data)
        return response_

    @private_user.delete('/<pk>', strict_slashes=True)
    @openapi.tag("admin")
    @openapi.summary("Удаление пользователя")
    @openapi.description("Удаление пользователя")
    @openapi.response(204, description='Successful Response')
    @openapi.response(400, {"application/json": ErrorResponseModel}, description='Bad Request')
    @openapi.response(401, {"application/json": 'Response 401 Private Delete User Private Users  Pk  Delete'})
    @openapi.response(403, {"application/json": 'Response 403 Private Delete User Private Users  Pk  Delete'})
    @openapi.response(422, {"application/json": HTTPValidationError}, description='Validation Error')
    @openapi.parameter("pk", int, location="query")
    @request_validation(check_token=True, check_pk=True)
    async def private_delete_user_private_users__pk__delete(request, pk):
        pk = int(pk)
        login_by_token = verify_token(di, request.cookies.get("token"))
        await check_admin(di, login_by_token)

        sql = delete(User.__table__).where(User.id == pk)
        await di.db.exec(sql)
        return text('Successful Response', status=204)

    @private_user.patch('/<pk>', strict_slashes=True)
    @openapi.tag("admin")
    @openapi.summary("Изменение информации о пользователе")
    @openapi.description("Здесь администратор может изменить любую информацию о пользователе")
    @openapi.response(200, {"application/json": PrivateDetailUserResponseModel}, description='Successful Response')
    @openapi.response(400, {"application/json": ErrorResponseModel}, description='Bad Request')
    @openapi.response(401, {"application/json": 'Response 401 Private Delete User Private Users  Pk  Delete'})
    @openapi.response(403, {"application/json": 'Response 403 Private Delete User Private Users  Pk  Delete'})
    @openapi.response(422, {"application/json": HTTPValidationError}, description='Validation Error')
    @openapi.parameter("pk", int, location="query")
    @validate(json=PrivateUpdateUserModel)
    @request_validation(check_token=True, check_pk=True)
    async def private_patch_user_private_users__pk__patch(request, pk, body: PrivateUpdateUserModel):
        login_by_token = verify_token(di, request.cookies.get("token"))
        await check_admin(di, login_by_token)

        body = body.dict()
        body['birthday'] = find_date(body['birthday'])
        sql = update(User.__table__).where(User.id == int(pk))
        await di.db.update(sql, body)
        body['id'] = int(pk)
        ser_data = json_.dumps(body, default=json_serial)
        data = json_.loads(ser_data)
        try:
            user_ = PrivateDetailUserResponseModel(**data)
        except ValidationError as e:
            print(e.json())
            raise exceptions.SanicException("Validation Error", status_code=422)
        response_ = json(user_.dict())
        return response_

    return private_user
