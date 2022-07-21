from typing import List, Union
from sqlalchemy.orm import Session

from app.sql import models as sql_models
from app import models as py_models

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_user(db: Session, user_id: int) -> sql_models.User:
    return db.query(sql_models.User).filter(sql_models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> sql_models.User:
    return db.query(sql_models.User).filter(sql_models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[sql_models.User]:
    return db.query(sql_models.User).offset(skip).limit(limit).all()


def add_user(db: Session, user: py_models.UserIn) -> sql_models.User:
    db_user = sql_models.User(
        email=user.email,
        hashed_password=pwd_context.hash(user.password)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def update_user(db: Session, user_id: int, update: py_models.UserUpdate) -> Union[sql_models.User, None]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    if update.new_password:
        db_user.hashed_password = pwd_context.hash(update.new_password)

    db.commit()
    db.refresh(db_user)

    return db_user


def del_user(db: Session, user_id: int) -> bool:
    db_user = get_user(db, user_id)

    if not db_user:
        return False

    db.delete(db_user)
    db.commit()

    return True


def activate_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    db_user.active = True

    db.commit()


def add_user_token(db: Session, token: str, user_id: int):
    db_token = sql_models.Token(token=token, owner_id=user_id)

    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    return db_token


def del_user_token(db: Session, token: str, user_id: int) -> bool:
    db_token = db.query(sql_models.Token).\
        filter(sql_models.Token.owner_id == user_id).\
        filter(sql_models.Token.token == token).\
        first()

    if not db_token:
        return False

    db.delete(db_token)
    db.commit()

    return True


def check_user_token(db: Session, token: str, user_id: int) -> bool:
    db_token = db.query(sql_models.Token).\
        filter(sql_models.Token.owner_id == user_id).\
        filter(sql_models.Token.token == token).\
        first()

    if db_token:
        return True
    return False
