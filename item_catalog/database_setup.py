from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Numeric, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime


Base = declarative_base()

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
    gid = Column(BigInteger, nullable = False)
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
    description = Column(String)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    date_created = Column(DateTime)
    date_updated = Column(DateTime)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

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
    filename = Column(String, nullable=False)
    item_id = Column(Integer, ForeignKey('item.id'))

    item = relationship("Item", back_populates="photos")

Item.photos = relationship(
    "Photo", order_by=Photo.id, back_populates="item")





engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)











