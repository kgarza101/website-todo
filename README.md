# My Todo App

A task management application built with Reflex.

## Features
- User authentication
- Task management (create, read, update, delete)
- Role-based access control (Manager and Assignee roles)
- Task status tracking
- Group-based task organization

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database and Run the app:
```bash
reflex db init
reflex db makemigrations
reflex db migrate
reflex run
```



## Database

The app uses SQLModel/SQLAlchemy for database operations. 
## License

MIT 
