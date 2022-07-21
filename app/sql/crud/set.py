from typing import Union, List

from sqlalchemy.orm import Session

from app.sql import models as sql_models
from app.sql.crud import user as crud_user
from app import models as py_models


def add_set(db: Session, card_set: py_models.Set, user: py_models.UserBase) -> Union[sql_models.Set, None]:
    # Make sure card IDs are unique
    id_set = set()
    for card in card_set.cards:
        if card.id in id_set:
            return None
        id_set.add(card.id)

    # Replace existing set if set ID exists
    existing_set = get_set(db, user, card_set.id)
    if existing_set:
        db.delete(existing_set)

    db_user = crud_user.get_user_by_email(db, user.email)

    db_set = sql_models.Set(
        id=card_set.id,
        name=card_set.name,
        type=card_set.type,
        max_question=card_set.max_question,
        question_time=card_set.question_time,
        owner_id=db_user.id
    )
    db.add(db_set)

    for card in card_set.cards:
        db_card = sql_models.Card(
            id=card.id,
            question=card.question,
            answer=card.answer,
            voice_address=card.voice_address,
            picture_address=card.picture_address,
            set_id=db_set.id
        )
        db.add(db_card)

    db.commit()
    db.refresh(db_set)

    return db_set


def get_sets(db: Session, user: py_models.UserBase, skip: int = 0, limit: int = 100) -> List[sql_models.Set]:
    user_db = crud_user.get_user_by_email(db, user.email)

    return db.query(sql_models.Set).\
        filter(sql_models.Set.owner_id == user_db.id).\
        offset(skip).\
        limit(limit).\
        all()


def get_set(db: Session, user: py_models.UserBase, id: int) -> sql_models.Set:
    user_db = crud_user.get_user_by_email(db, user.email)

    return db.query(sql_models.Set).\
        filter(sql_models.Set.owner_id == user_db.id).\
        filter(sql_models.Set.id == id).\
        first()


def del_set(db: Session, user: py_models.UserBase, id: int) -> bool:
    set = get_set(db, user, id)
    if not set:
        return False

    db.delete(set)
    db.commit()
    return True


def get_card(db: Session, set: sql_models.Set, id: int) -> sql_models.Card:
    return db.query(sql_models.Card).\
        filter(sql_models.Card.set_id == set.id).\
        filter(sql_models.Card.id == id).\
        first()
