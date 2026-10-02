Employee & Leave Management System

A backend REST API for managing employees, departments, users, and employee leave requests.

Technologies Used
- Python 3.9+
- FastAPI
- Pydantic
- SQLAlchemy
- MySQL
- Alembic
- JWT Authentication
- Passlib / bcrypt
- Uvicorn

Project Structure

Employee_Leave_Management/
    app/
        main.py
        database.py
        models/
        schemas/
        routers/
        services/
        auth/
    alembic/
    alembic.ini
    .env
    .env.example
    .gitignore
    requirements.txt
    README.md

Features

Authentication
- User registration
- User login
- JWT authentication
- Role-based access control
- Admin, HR, and Employee roles
- Password hashing

Department Management
- Create departments
- View departments
- Update departments
- Soft delete departments

Employee Management
- Create employees
- View employees
- Update employees
- Soft delete employees
- Search
- Filtering
- Sorting
- Pagination

Leave Management
- Apply for leave
- View own leaves
- Approve leave
- Reject leave
- Cancel leave
- Sick, Casual, and Earned leave
- Leave balance validation
- Weekdays-only calculation
- Leave overlap validation

Reports
- Dashboard
- Employee statistics
- Department statistics
- Leave status summary
- Employee-wise leave balance

Leave Limits
- Sick: 12 days
- Casual: 10 days
- Earned: 15 days

Running the Application

uvicorn app.main:app --reload

API:
http://127.0.0.1:8000

Swagger:
http://127.0.0.1:8000/docs

API Modules
- /auth
- /departments
- /employees
- /leaves
- /reports

Security
- Passwords are hashed.
- JWT tokens expire after 30 minutes.
- .env is excluded from Git.
- Role-based authorization is implemented.