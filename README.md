# Library Management Backend

A FastAPI-based backend for a library system with user authentication, book management, wishlists, rentals, admin/staff actions, and robust database schema.

## Features
- User registration, login, and email confirmation
- Book search and management
- User wishlists
- Book rentals and returns
- Admin/staff actions (bulk upload, rental management, reporting)
- Email notifications
- Synchronous SQLAlchemy ORM
- Alembic migrations
- Full API test suite

## Getting Started

### 1. Clone the repository
```bash
git clone <repo-url>
cd LibProject
```

### 2. Install dependencies

#### Using Poetry
```bash
poetry install
poetry shell
```

#### Using pip
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file with the following (example):
```
DATABASE_URL=sqlite:///library.db
ADMIN_EMAIL=admin@example.com
HOST=http://localhost
PORT=8000
BOOK_RENTAL_DUE_DAYS=30
```

### 4. Run database migrations
```bash
alembic upgrade head
```

### 5. Start the server
```bash
uvicorn main:app --reload
```

### 6. Run tests
```bash
pytest
```

---

## API Endpoints

### Auth Endpoints (`/api/v1/auth`)
- `POST /login` — User login (returns access/refresh tokens)
- `POST /register` — Register a new user
- `GET /confirm-email` — Confirm user email with token
- `POST /resend-confirmation` — Resend email confirmation

### User Endpoints (`/api/v1/user`)
- `GET /wishlist` — Get current user's wishlist
- `POST /wishlist?book_id=...` — Add a book to wishlist
- `DELETE /wishlist/{book_id}` — Remove a book from wishlist
- `GET /search?author=...&title=...` — Search books by author/title
- `POST /request-staff-access` — Request staff privileges

### Admin Endpoints (`/api/v1/admin`)
- `GET /confirm-staff-access?token=...` — Confirm staff access for a user
- `POST /books/bulk-create` — Bulk upload books via CSV (staff only)
- `POST /rental` — Rent a book to a user (staff only)
- `POST /rental/return` — Return a rented book (staff only)
- `POST /rental/extend` — Extend a book rental (staff only)
- `GET /rental/report` — Get rental report (staff only, supports `username` param)

---

## Notes
- All endpoints requiring authentication expect a Bearer token in the `Authorization` header.
- Admin endpoints require the user to have staff privileges.
- Email sending and some admin actions require proper environment configuration.
- For development, SQLite is used by default, but you can configure any SQLAlchemy-supported database.

---

## License
MIT
