from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.sql.database import Base


class Set(Base):
    __tablename__ = 'sets'

    uid = Column(Integer, primary_key=True, index=True)
    id = Column(Integer, index=True)
    type = Column(String)
    name = Column(String)
    max_question = Column(Integer)
    question_time = Column(Float)
    owner_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship('User', back_populates='sets')
    cards = relationship('Card', back_populates='set', cascade='all, delete')


class Card(Base):
    __tablename__ = 'cards'

    uid = Column(Integer, primary_key=True, index=True)
    id = Column(Integer, index=True)
    question = Column(String)
    answer = Column(String)
    voice_address = Column(String)
    picture_address = Column(String)
    set_id = Column(Integer, ForeignKey('sets.id'))

    set = relationship('Set', back_populates='cards')
