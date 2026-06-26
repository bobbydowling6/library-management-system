from sqlalchemy import create_engine, String, Text, ForeignKey, Table, Column, Integer, DateTime, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from typing import Optional, List
import datetime

engine = create_engine("sqlite:///library_management_system.db", echo=True)

class Base(DeclarativeBase):
    pass

# Association table for many-to-many relationship between books and authors
books_authors = Table(
    "books_authors",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)

class Books(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    isbn: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    year_published: Mapped[str] = mapped_column(String(100), nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, nullable=False)

    authors: Mapped[List["Authors"]] = relationship(
        "Authors",
        secondary=books_authors,
        back_populates="books",
    )

    borrowings: Mapped[List["Borrowing"]] = relationship(
        "Borrowing",
        back_populates="book",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Book(title='{self.title}')"

class Authors(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    books: Mapped[List[Books]] = relationship(
        "Books",
        secondary=books_authors,
        back_populates="authors",
    )

    def __repr__(self) -> str:
        return f"Author(name='{self.name}')"

class Members(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    membership_date: Mapped[str] = mapped_column(String(100), nullable=False)

    borrowings: Mapped[List["Borrowing"]] = relationship(
        "Borrowing",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Member(name='{self.name}')"

class Borrowing(Base):
    __tablename__ = "borrowings"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id"), nullable=False)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id"), nullable=False)
    checkout_date: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    return_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    book: Mapped[Books] = relationship("Books", back_populates="borrowings")
    member: Mapped[Members] = relationship("Members", back_populates="borrowings")

    def __repr__(self) -> str:
        return f"Borrowing(book_id={self.book_id}, member_id={self.member_id})"


# Helper functions for member borrowings
LOAN_DAYS = 14

def get_member_by_email(session: Session, email: str) -> Optional[Members]:
    return session.scalar(select(Members).where(Members.email == email))

def list_member_borrowings(session: Session, *, member_email: Optional[str] = None, member_id: Optional[int] = None, only_active: bool = False):
    if member_email:
        member = session.scalar(select(Members).where(Members.email == member_email))
        if not member:
            return []
        member_id = member.id
    if member_id is None:
        return []

    q = select(Borrowing).where(Borrowing.member_id == member_id).order_by(Borrowing.checkout_date.desc())
    if only_active:
        q = q.where(Borrowing.return_date == None)
    results = session.scalars(q).all()
    return results

def list_overdue_borrowings(session: Session, days: int = LOAN_DAYS):
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    q = select(Borrowing).where(Borrowing.return_date == None).where(Borrowing.checkout_date < cutoff)
    return session.scalars(q).all()

def checkout_book(session: Session, book_id: int, member_id: int):
    book = session.get(Books, book_id)
    member = session.get(Members, member_id)
    if not book or not member:
        raise ValueError("Invalid book or member id")
    if book.available_copies < 1:
        raise ValueError("No copies available")
    book.available_copies -= 1
    borrowing = Borrowing(book=book, member=member, checkout_date=datetime.datetime.now(), return_date=None)
    session.add(borrowing)
    session.commit()
    return borrowing

def return_book(session: Session, borrowing_id: int):
    borrowing = session.get(Borrowing, borrowing_id)
    if not borrowing:
        raise ValueError("Borrowing not found")
    if borrowing.return_date is not None:
        return borrowing
    borrowing.return_date = datetime.datetime.now()
    # increment book copies
    borrowing.book.available_copies += 1
    session.commit()
    return borrowing


def create_sample_data():
    with Session(engine) as session:
        existing = session.execute(select(Authors)).first()
        if existing:
            print("Sample data already exists, skipping creation.")
            return

        # Authors
        a1 = Authors(name="J.K. Rowling", bio="Author of the Harry Potter series")
        a2 = Authors(name="J.R.R. Tolkien", bio="Author of The Lord of the Rings")
        a3 = Authors(name="Isaac Asimov", bio="Science fiction author")
        a4 = Authors(name="F. Scott Fitzgerald", bio="Author of The Great Gatsby and The Side of Paradise")

        # Books
        b1 = Books(title="Harry Potter and the Philosopher's Stone", isbn="9780747532699", year_published="1997", available_copies=3)
        b2 = Books(title="The Hobbit", isbn="9780261102217", year_published="1937", available_copies=2)
        b3 = Books(title="Foundation", isbn="9780553293357", year_published="1951", available_copies=1)
        b4 = Books(title="The Great Gatsby", isbn="9783485768445", year_published="1925", available_copies=3)
        b5 = Books(title="The Side of Paradise", isbn="9780174927312", year_published="1920", available_copies=2)

        # link books and authors (many-to-many)
        b1.authors.append(a1)
        b2.authors.append(a2)
        b3.authors.append(a3)
        b4.authors.append(a4)
        b5.authors.append(a4)

        # Members
        m1 = Members(name="Alice Smith", email="alice@example.com", membership_date="2024-01-15")
        m2 = Members(name="Bob Jones", email="bob@example.com", membership_date="2025-03-22")
        m3 = Members(name="Bill Packard", email="bill@example.com", membership_date="2023-03-10")
        m4 = Members(name="Brian Williams", email="brian@example.com", membership_date="2025-05-29")

        session.add_all([a1, a2, a3, a4, b1, b2, b3,b4, b5, m1, m2, m3, m4])
        session.commit()

        # Borrowings (one active, one returned)
        now = datetime.datetime.now()
        borrow1 = Borrowing(book=b1, member=m1, checkout_date=now - datetime.timedelta(days=10), return_date=None)
        borrow2 = Borrowing(book=b2, member=m2, checkout_date=now - datetime.timedelta(days=20), return_date=now - datetime.timedelta(days=5))
        borrow3 = Borrowing(book=b3, member=m3, checkout_date=now - datetime.timedelta(days=20), return_date=now - datetime.timedelta(days=5))
        borrow4 = Borrowing(book=b4, member=m1, checkout_date=now - datetime.timedelta(days=20), return_date=now - datetime.timedelta(days=5))
        borrow5 = Borrowing(book=b5, member=m4, checkout_date=now - datetime.timedelta(days=20), return_date=now - datetime.timedelta(days=5))
        borrow6 = Borrowing(book=b5, member=m4, checkout_date=now - datetime.timedelta(days=20), return_date=now - datetime.timedelta(days=5))

        session.add_all([borrow1, borrow2, borrow3, borrow4, borrow5, borrow6])
        session.commit()
        print("Sample data created: 4 authors, 5 books, 4 members, 6 borrowings")


def init_db():
    """Create database tables for the library system."""
    Base.metadata.create_all(engine)


def get_or_create_member(session: Session, *, name: str, email: str, membership_date: Optional[str] = None) -> Members:
    """Return existing Members by email or create a new one.

    Commits the session when a new member is created.
    """
    membership_date = membership_date or datetime.date.today().isoformat()
    member = session.scalar(select(Members).where(Members.email == email))
    if member:
        return member
    member = Members(name=name, email=email, membership_date=membership_date)
    session.add(member)
    session.commit()
    return member
