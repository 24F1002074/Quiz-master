# Quiz Master Application

A web-based quiz application that allows users to create, manage, and participate in quizzes. Built with Flask and SQLAlchemy.

## Features

- User authentication and authorization
- Create and manage quizzes
- Take quizzes and view results
- Track user progress and scores
- Admin dashboard for quiz management

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quiz_master.git
cd quiz_master
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root and add:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///quiz.db
```

2. Start the application (choose one method):

Method 1 - Using Flask CLI:
```bash
flask run
```

Method 2 - Using Python directly:
```bash
python app.py
```

3. Access the application at `http://localhost:5000`


## Project Structure

```
quiz_master/
├── app/
│   ├── models/
│   ├── controllers/
│   ├── templates/
│   └── static/
├── requirements.txt
└── README.md
```
