🎯 Quiz Master – V1

Quiz Master – V1 is a Flask-based multi-user quiz management web application designed to help students prepare for exams through structured quizzes while giving administrators full control over content and performance tracking.

It provides a smooth and interactive learning experience with role-based access, performance analytics, and a modular backend architecture.

🚀 Features
👨‍🎓 User Features

User registration and login

Attempt quizzes by subject and chapter

Automatic score calculation

View past quiz attempts and performance history

Visual performance insights using charts

🛠️ Admin Features

Secure admin login

Create and manage subjects and chapters

Create quizzes with multiple-choice questions

Manage users

Track overall user performance

🧱 Tech Stack
Layer	Technology
Backend	Flask
Database	SQLite
ORM	Flask-SQLAlchemy
Frontend	HTML, Bootstrap
Charts & Analytics	Chart.js
Architecture	MVC Pattern with Flask Blueprints
🗄️ Database Schema Overview

Users – Stores user credentials and roles (Admin/User)

Subjects – Available subjects

Chapters – Chapters linked to subjects

Quizzes – Quiz details (subject, chapter, duration, etc.)

Questions – MCQ questions and correct answers

User Attempts – Stores quiz scores and timestamps

🔌 API Support

The application includes RESTful APIs for:

Subjects Management

Chapters Management

Quizzes Management

Questions Management

User Attempts & Results

These APIs allow smooth communication between frontend and backend.

🧩 Project Architecture

The project follows the MVC (Model-View-Controller) design pattern:

Models – Database models using SQLAlchemy

Views – HTML templates with Bootstrap

Controllers – Flask routes handling application logic

Blueprints – Modular structure for scalability

📊 Data Visualization

Chart.js is used to display:

Quiz attempts per subject (User Dashboard)

Average top scores per subject (Admin Dashboard)

Number of quizzes per subject

▶️ Demo Video

📽️ Project walkthrough:
https://drive.google.com/file/d/1YPqyo6KTPsjaCsouGOXEWvAC9rX11Ix1/view

⚙️ How to Run the Project Locally
# Clone the repository
git clone https://github.com/AaryeshShukla/Quiz-Master---V1.git

# Navigate into the project folder
cd Quiz-Master---V1

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py


Then open your browser and go to:

http://127.0.0.1:5000
