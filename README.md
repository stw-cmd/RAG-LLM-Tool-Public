# UFCFFF-30-2 Software Development Project: Retrieval-Augmented Generation Large Language Model Tool

Author: Samuel Williams

A Flask-based web application for **Retrieval-Augmented Generation** (RAG) that lets users upload documents (PDF, text, etc.), scrape websites, and ask questions grounded in their own content. Built with Flask, SQLAlchemy, Flask-Migrate, LangChain, ChromaDB, and OpenAI.

---

## Features

- **User Accounts**: Registration, login, password reset via tokenised email links.
- **Document Management**: Upload local files, scrape website text; documents are chunked, vectorised, and stored in per-user ChromaDB stores.
- **Query Interface**: Ask questions and get answers powered by an LLM + retrieval from your own documents. History of Q&A is saved.
- **Folder Organisation**: Create, rename, delete folders and assign documents to them.
- **Admin Dashboard**: Site-wide metrics, user lookup, promote/demote admin roles, charts for user growth, documents, and queries.
- **Dark/Light Themes**: User-selectable colour modes.

## Tech Stack

- **Flask** – Web framework
- **Flask-Login** – Authentication
- **Flask-Mail** – Email sending (password resets)
- **Flask-Migrate / Alembic** – Database migrations
- **SQLAlchemy** – ORM (SQLite by default)
- **LangChain** – Document chunking & RAG pipeline
- **ChromaDB** – Vector store for embeddings
- **OpenAI** – LLM and embeddings
- **Tailwind CSS & FontAwesome** – Frontend styling

## Prerequisites

- Python 3.10+
- pip
- OAuth/OpenAI API key
- (Optional) Docker, if you prefer containerised setup

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-org/RAG-LLM-Tool.git
cd RAG-LLM-Tool
```

### 2. Create a virtual environment & install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment variables

Copy the example env file and fill in your secrets:

```bash
cp .env.example .env
# Then edit .env to set:
# SECRET_KEY, WTF_CSRF_SECRET_KEY
# DATABASE_URL (e.g. sqlite:///instance/app.db)
# OPENAI_API_KEY
# MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD
# ADMIN_SECRET_CODE
```

### 4. Configuration

All settings are loaded from `app/config.py`, which reads your `.env`. By default it will:

- Use `DATABASE_URL` for SQLAlchemy. If unset, fall back to `sqlite:///instance/app.db`.
- Load Flask, mail, and OpenAI keys from environment.

### 5. Database setup & migrations

Ensure the `instance/` folder exists and is writable:

```bash
mkdir -p instance
```

Run migrations:

```bash
export FLASK_APP=run.py
export FLASK_ENV=development
flask db upgrade
```

This creates your `app.db` file in `instance/`.

### 6. Running the app

```bash
# Development server
python run.py
```

Then open <http://127.0.0.1:5500> in your browser.

### 7. Promoting a user to admin

By default, newly registered users will not have admin privileges (boolean column 'is_admin' set to false)
After running the python file `run.py`, run call in terminal: 

```bash
flash promote-admin
```
Followed by entering the email of the user to promote to admin.

This method of promotion is only required for the first admin user, as the admin dashboard is protected by login. Future promotions can be done via the admin dashboard (user lookup table).

## Project Structure

```
RAG-LLM-Tool/
├── app/
│   ├── auth/          # Registration, login, password reset
│   ├── documents/     # Uploading, scraping, folder management
│   ├── queries/       # RAG pipeline & Q&A history
│   ├── admin/         # Admin dashboard & user management
│   ├── models.py      # SQLAlchemy models
│   ├── config.py      # App configuration
│   ├── extensions.py  # DB & Mail init
│   ├── utils.py       # Helpers (Pandoc, NLTK, Chroma helpers)
│   └── templates/     # Jinja2 templates (base, dashboard, forms…)
├── migrations/        # Alembic migration scripts
├── instance/          # runtime files (SQLite DB)
├── static/            # Tailwind output, JS
├── run.py             # App entrypoint
├── requirements.txt   # Python dependencies
├── .gitignore         # Specifies intentionally untracked files that Git should ignore
├── package.json       # Main configuration file for Node.js
├── package-lock.json  # Locks the entire dependency tree of node modules to specific versions
├── postcss.config.js  # Declares PostCSS plugins (tailwind, etc.)
├── .env.example       # Environment variable template
└── README.md          # (you are here)
```

## Usage

1. **Register** a new account.
2. **Upload** documents or **scrape** a website URL.
3. In the **Query** pane, type a question and submit. Answers will be grounded in your uploaded content.
4. View query history, delete entries, organise documents into folders.
5. As an admin, visit `/admin/dashboard` to see global metrics and manage users.

## Testing

Run the pytest suite:

```bash
pytest
```

This code and associated materials are provided solely for assessment purposes.
