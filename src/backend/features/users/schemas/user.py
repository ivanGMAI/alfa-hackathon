from pydantic import BaseModel, EmailStr


class UserRegisterSchema(BaseModel):
    name: str
    surname: str
    patronymic: str
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    user_id: int
    email: EmailStr


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
