from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, constr


class LoginModel(BaseModel):
    login: constr(strict=True)
    password: constr(strict=True)


class CurrentUserResponseModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    is_admin: bool
    other_name: Optional[str]
    phone: Optional[str]
    birthday: Optional[date]


class ErrorResponseModel(BaseModel):
    code: int
    message: str


class Loc(BaseModel):
    loc: str


class ValidationError(BaseModel):
    loc: List[Loc]
    msg: str
    type: str


class HTTPValidationError(BaseModel):
    detail: List[ValidationError]


class UsersListElementModel(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr


class PaginatedMetaDataModel(BaseModel):
    total: int
    page: int
    size: int


class UsersListMetaDataModel(BaseModel):
    pagination: PaginatedMetaDataModel


class UsersListResponseModel(BaseModel):
    data: List[UsersListElementModel]
    meta: UsersListMetaDataModel


class CRUDUsersListResponseModel(UsersListResponseModel):
    @staticmethod
    def create(users, total_pages, page, size):
        return UsersListResponseModel(
            data=users,
            meta=UsersListMetaDataModel(
                pagination=PaginatedMetaDataModel(
                    total=total_pages,
                    page=page,
                    size=size
                )
            )
        )


class UpdateUserModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    other_name: Optional[str]
    phone: Optional[str]
    birthday: Optional[str]


class UpdateUserResponseModel(UpdateUserModel):
    id: int
    birthday: Optional[date]


class CitiesHintModel(BaseModel):
    id: int
    name: str


class PrivateUsersListHintMetaModel(BaseModel):
    city: List[CitiesHintModel]


class PrivateUsersListMetaDataModel(BaseModel):
    pagination: PaginatedMetaDataModel
    hint: PrivateUsersListHintMetaModel


class PrivateUsersListResponseModel(BaseModel):
    data: List[UsersListElementModel]
    meta: PrivateUsersListMetaDataModel


class CRUDPrivateUsersListResponseModel(PrivateUsersListResponseModel):
    @staticmethod
    def create(data, page, size, total, cities):
        return PrivateUsersListResponseModel(
            data=data,
            meta=PrivateUsersListMetaDataModel(
                pagination=PaginatedMetaDataModel(
                    size=size,
                    page=page,
                    total=total
                ),
                hint=PrivateUsersListHintMetaModel(
                    city=cities
                )

            )
        )


class CitiesCreate(BaseModel):
    name: str


class PrivateUser(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    is_admin: bool
    other_name: Optional[str] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None
    city: Optional[int] = None
    additional_info: Optional[str] = None


class PrivateCreateUserModel(PrivateUser):
    password: str


class PrivateDetailUserResponseModel(PrivateUser):
    id: int
    birthday: Optional[str]


class PrivateUpdateUserModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    is_admin: bool
    other_name: Optional[str]
    phone: Optional[str]
    birthday: Optional[str]
    city: Optional[int]
    additional_info: Optional[str]
