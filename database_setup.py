import sys

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

from datetime import datetime

from flask_login import UserMixin

Base = declarative_base()


class User(Base, UserMixin):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    token = Column(Text)

    item = relationship('Item', backref="user", uselist=True)


class Category(Base):
    __tablename__ = 'category'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)

    item = relationship('Item', backref="category", uselist=True)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class Item(Base):
    __tablename__ = 'item'

    title = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    created_on = Column(DateTime, nullable=True, default=datetime.now())

    cat_id = Column(Integer, ForeignKey('category.id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('user.id'))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'cat_id': self.cat_id,
            'user_id':self.user_id
        }

engine = create_engine(
    'sqlite:///catalog.db')

Base.metadata.create_all(engine)
