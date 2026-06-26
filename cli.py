from library_system import (
    Session,
    engine,
    init_db,
    create_sample_data,
    list_member_borrowings,
    list_overdue_borrowings,
    checkout_book,
    return_book,
    Books,
    Members,
    Borrowing,
    get_or_create_member,
)
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
import datetime


def add_book_interactive(session: Session):
    title = input("Title: ")
    isbn = input("ISBN: ")
    year = input("Year published: ")
    copies = int(input("Available copies: ").strip() or "1")
    book = Books(title=title, isbn=isbn, year_published=year, available_copies=copies)
    session.add(book)
    session.commit()
    print(f"Added book id={book.id} title={book.title}")
    # confirm saved in DB
    saved = session.get(Books, book.id)
    if saved:
        print(f"Confirmed in DB: id={saved.id} title={saved.title} isbn={saved.isbn} copies={saved.available_copies}")
    else:
        print("Warning: could not confirm book in DB")


def add_member_interactive(session: Session):
    name = input("Member name: ").strip()
    email = input("Email: ").strip()
    membership_date = input("Membership date (YYYY-MM-DD): ").strip() or datetime.date.today().isoformat()

    member = get_or_create_member(session, name=name, email=email, membership_date=membership_date)
    if member:
        print(f"Member ready: id={member.id} name={member.name} email={member.email}")
    else:
        print("Failed to create or retrieve member")


def search_books_interactive(session: Session):
    term = input("Search term (title or isbn): ").strip()
    q = select(Books).where(Books.title.ilike(f"%{term}%") | Books.isbn.ilike(f"%{term}%"))
    results = session.scalars(q).all()
    if not results:
        print("No books found")
        return
    for b in results:
        print(f"{b.id}: {b.title} (ISBN {b.isbn}) copies={b.available_copies}")
    print(f"Displayed {len(results)} book(s)")


def checkout_book_interactive(session: Session):
    try:
        book_id = int(input("Book id to check out: ").strip())
        member_id = int(input("Member id: ").strip())
        borrowing = checkout_book(session, book_id=book_id, member_id=member_id)
        print(f"Checked out id={borrowing.id}")
        # confirm borrowing and updated book copies
        saved = session.get(Borrowing, borrowing.id)
        if saved:
            print(f"Confirmed borrowing id={saved.id} book_id={saved.book_id} member_id={saved.member_id} checkout={saved.checkout_date}")
            # refresh book
            book = session.get(Books, saved.book_id)
            if book:
                print(f"Book '{book.title}' now has {book.available_copies} available copies")
        else:
            print("Warning: could not confirm borrowing in DB")
    except Exception as e:
        print("Error:", e)


def return_book_interactive(session: Session):
    try:
        borrowing_id = int(input("Borrowing id to return: ").strip())
        borrowing = return_book(session, borrowing_id=borrowing_id)
        print(f"Returned borrowing id={borrowing.id}")
        # confirm return and updated book copies
        saved = session.get(Borrowing, borrowing.id)
        if saved:
            status = 'Returned' if saved.return_date else 'Checked out'
            print(f"Confirmed borrowing id={saved.id} status={status} return_date={saved.return_date}")
            book = session.get(Books, saved.book_id)
            if book:
                print(f"Book '{book.title}' now has {book.available_copies} available copies")
        else:
            print("Warning: could not confirm borrowing in DB")
    except Exception as e:
        print("Error:", e)


def view_member_borrowings_interactive(session: Session):
    email = input("Member email: ").strip()
    borrows = list_member_borrowings(session, member_email=email)
    if not borrows:
        print("No borrowings found for that member")
        return
    for b in borrows:
        status = "Returned" if b.return_date else "Checked out"
        print(f"{b.id}: {b.book.title} | checkout={b.checkout_date} | return={b.return_date} | {status}")
    print(f"Displayed {len(borrows)} borrowing(s) for member {email}")


def view_overdue_interactive(session: Session):
    overdue = list_overdue_borrowings(session)
    if not overdue:
        print("No overdue borrowings")
        return
    for b in overdue:
        days_over = (datetime.datetime.now() - b.checkout_date).days
        print(f"{b.id}: {b.book.title} | member={b.member.name} | checked out {b.checkout_date.date()} ({days_over} days ago)")
    print(f"Displayed {len(overdue)} overdue borrowing(s)")


def print_existing_data(session: Session):
    # counts
    books_count = session.scalar(select(func.count()).select_from(Books))
    members_count = session.scalar(select(func.count()).select_from(Members))
    borrowings_count = session.scalar(select(func.count()).select_from(Borrowing))
    print(f"Database summary: {books_count} book(s), {members_count} member(s), {borrowings_count} borrowing(s)")
    # show a few recent borrowings
    recent = session.scalars(select(Borrowing).order_by(Borrowing.checkout_date.desc()).limit(5)).all()
    if recent:
        print("Recent borrowings:")
        for b in recent:
            status = "Returned" if b.return_date else "Checked out"
            print(f"- {b.id}: {b.book.title} by {b.member.name} on {b.checkout_date.date()} ({status})")
    else:
        print("No borrowings yet")


def run_cli():
    init_db()
    create_sample_data()
    # print a quick summary of existing data before showing the menu
    with Session(engine) as session:
        print_existing_data(session)

    while True:
        print("📚 Library Management System")
        print("1. Add a book")
        print("2. Add a member")
        print("3. Search books")
        print("4. Check out a book")
        print("5. Return a book")
        print("6. View member's borrowings")
        print("7. View overdue books")
        print("8. Exit")
        choice = input("Choose an option (or type member email to view borrowings): ").strip()
        with Session(engine) as session:
            # allow typing a member email directly at the main prompt
            if "@" in choice and "." in choice:
                borrows = list_member_borrowings(session, member_email=choice)
                if not borrows:
                    print("No borrowings found for that member")
                else:
                    for b in borrows:
                        status = "Returned" if b.return_date else "Checked out"
                        print(f"{b.id}: {b.book.title} | checkout={b.checkout_date} | return={b.return_date} | {status}")
                continue
            if choice == "1":
                add_book_interactive(session)
            elif choice == "2":
                add_member_interactive(session)
            elif choice == "3":
                search_books_interactive(session)
            elif choice == "4":
                checkout_book_interactive(session)
            elif choice == "5":
                return_book_interactive(session)
            elif choice == "6":
                view_member_borrowings_interactive(session)
            elif choice == "7":
                view_overdue_interactive(session)
            elif choice == "8":
                print("Goodbye")
                break
            else:
                print("Invalid choice")


if __name__ == "__main__":
    run_cli()
