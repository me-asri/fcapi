from typing import List

from pydantic import BaseModel, Field


class Card(BaseModel):
    id: int = Field(..., example=1)
    question: str = Field(..., example='What does 光る mean?')
    answer: str = Field(..., example='To shine')
    voice_address: str = Field('')
    picture_address: str = Field('')

    class Config:
        orm_mode = True


class CardDb(Card):
    uid: int = Field(..., example=1)
    set_id: int = Field(..., example=1)


class Set(BaseModel):
    id: int = Field(..., example=1)
    name: str = Field(..., example='Japanese Set')
    type: str = Field(..., example='Listening')
    max_question: int = Field(..., example=5)
    question_time: float = Field(..., example=50.0)

    cards: List[Card]

    class Config:
        orm_mode = True


class SetDb(Set):
    uid: int = Field(..., example=1)
    owner_id: int = Field(..., example=1)
