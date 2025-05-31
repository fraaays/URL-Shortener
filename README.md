Flask URL Shortener 🔗


A simple and stylish URL shortener web application built with Flask, SQLite, and SQLAlchemy. It allows users to submit long URLs and get shortened versions, view a list of all shortened URLs, and delete them. Includes test coverage and responsive design.

Features ✨
🔗 Generate short links from long URLs

📜 List all shortened URLs

🗑️ Delete URLs from the list

🧪 Unit tested with 100% coverage using unittest

🎨 Clean, responsive UI using HTML + CSS

Tech Stack 🛠
Flask (Python web framework)

SQLite (Database)

SQLAlchemy (ORM)

HTML + CSS (Frontend)

unittest (Testing)

Setup & Run Locally 🚀
1. Clone the Repo
bash
Copy
Edit
git clone https://github.com/yourusername/flask-url-shortener.git
cd flask-url-shortener
2. Install Dependencies
It’s best to use a virtual environment.

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
3. Run the App
bash
Copy
Edit
python app.py
Then open your browser and go to:
http://127.0.0.1:5000

Usage 🧑‍💻
Paste your long URL into the input box.

Click "Shorten".

The app generates a short URL.

You can see a table of all URLs.

Click "Delete" to remove an entry.

Folder Structure 📁
graphql
Copy
Edit
flask-url-shortener/
│
├── app.py              # Main Flask application
├── models.py           # SQLAlchemy database model
├── templates/
│   └── index.html      # Frontend HTML page
├── static/             # (Optional) for extra CSS or JS
├── test_app.py         # Unit tests with 100% coverage
├── requirements.txt    # Python dependencies
└── README.md           # This file
Tests ✅
To run all unit tests (and reach 100% coverage):

bash
Copy
Edit
python -m unittest test_app.py
Includes tests for:

Valid and invalid URL submissions

Redirection logic

Database inserts and deletes

Error handling

Screenshots 🖼️

License 📜
MIT License
