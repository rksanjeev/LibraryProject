from sqlalchemy import Column, Integer, String, Enum, Table, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import enum
from db.models import Base
from datetime import datetime

class RentalStatusEnum(str, enum.Enum):
    available = "available"
    borrowed = "borrowed"

class BookModel(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(20), nullable=False, index=True)
    authors = Column(String(255), nullable=False)
    publication_year = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    language = Column(String(20), nullable=False)
    rental_status = Column(Enum(RentalStatusEnum), nullable=False, default=RentalStatusEnum.available)

    def __repr__(self):
        return f"<Book(id={self.id}, title={self.title}, authors={self.authors}, rental_status={self.rental_status})>"

# Association table for many-to-many relationship between users and books
wishlist_books = Table(
    'wishlist_books',
    Base.metadata,
    Column('wishlist_id', Integer, ForeignKey('wishlists.id'), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True)
)

class WishlistModel(Base):
    __tablename__ = 'wishlists'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    books = relationship('BookModel', secondary=wishlist_books, backref='wishlists')

    def __repr__(self):
        return f"<Wishlist(id={self.id}, user_id={self.user_id})>"

class RentalModel(Base):
    __tablename__ = 'rentals'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    rental_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Rental(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, rental_date={self.rental_date})>"