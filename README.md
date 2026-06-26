# library-management-system

A lightweight SQLite library management system with separated database logic and an interactive CLI.

## Project Files

- `library_system.py` — SQLAlchemy ORM models for `Books`, `Authors`, `Members`, and `Borrowings`; database initialization; helper functions such as
  - `init_db()`
  - `create_sample_data()`
  - `get_or_create_member()`
  - `list_member_borrowings()`
  - `list_overdue_borrowings()`
  - `checkout_book()`
  - `return_book()`
- `cli.py` — interactive command-line interface that imports the core library system and provides menu-driven actions, startup data summary output, and database confirmation prints.

## Setup

1. Activate the virtual environment:

```bash
source ./venv/bin/activate
```

2. Install dependencies using `requirements.txt`:

```bash
pip install -r requirements.txt
```

3. The app uses `sqlite:///library_management_system.db` by default, and `cli.py` will create the database tables automatically.

## Run the CLI

```bash
./venv/bin/python cli.py
```

When the CLI starts, it prints a short database summary and recent borrowings before showing the menu.

## CLI Menu

The interactive CLI supports the following options:

1. Add a book
2. Add a member
3. Search books
4. Check out a book
5. Return a book
6. View member's borrowings
7. View overdue books
8. Exit

You can also type a member email at the main prompt to view that member's borrowings directly.

## Notes

- `cli.py` now uses `get_or_create_member()` so adding a member with an existing email returns the existing record instead of raising a UNIQUE constraint error.
- `library_system.py` is designed to be imported independently of the CLI, making it easier to reuse or test database logic.
- Sample data is created automatically on first CLI run if the database is empty.

## Development

- Use the virtual environment:

```bash
source ./venv/bin/activate
```

- Check CLI syntax quickly:

```bash
./venv/bin/python -m py_compile cli.py
```

- Edit the core logic in `library_system.py` and the interface in `cli.py`.
- There are no automated tests yet, so running the CLI and trying each option is the current manual verification path.
