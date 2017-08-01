from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, \
    Numeric, BigInteger, LargeBinary, BLOB, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
        }

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    gid = Column(String(21), nullable = False)
    name = Column(String(80))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'gid': self.gid,
            'name': self.name,
        }
        
class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    price = Column(Float(scale=2))
    description = Column(String)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    date_created = Column(DateTime)
    date_updated = Column(DateTime)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    carts = relationship('Shopping_Cart_Item', cascade='all,delete', back_populates='item')

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'date_created': self.date_created.isoformat(' '),
            'date_updated': self.date_updated.isoformat(' '),
            'id': self.id,
            'user_id': self.user_id,
        }


class Photo(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('item.id'))
    public_url = Column(String)
    filename = Column(String)
    item = relationship("Item", back_populates="photos")

Item.photos = relationship(
    "Photo", order_by=Photo.id, back_populates="item")

class Shopping_Cart_Item(Base):
    __tablename__ = 'shopping_cart'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    item_id = Column(Integer, ForeignKey('item.id'))
    user = relationship(User)
    item = relationship(Item)

User.shopping_cart = relationship(
    "Shopping_Cart_Item")
