# URL Shortener

This is a simple URL shortener web application built with Flask and SQLite.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Features

- Shortens long URLs to a shorter and more manageable format.
- Stores the original and shortened URLs in a SQLite database.
- Redirects users to the original URL when they visit the shortened URL.

## Prerequisites

Make sure you have the following prerequisites installed on your local machine

- Python 3.x: [Download Python](https://www.python.org/downloads/)
- Flask: Install Flask by running `pip install flask` in your command line or terminal.
- SQLite: SQLite comes bundled with Python by default, so no additional installation is required.

## Installation

1. Clone the repository

   ```shell
    git clone https://github.com/ezhil56x/URL-Shortener.git
   ```

2. Navigate to the cloned repository

   ```shell
    cd URL-Shortener
   ```

3. Run the following command to start the application

   ```shell
    flask run
   ```

   or

   ```shell
    python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000/`

## Usage

1. Enter the URL you want to shorten in the text box and click on the `Shorten` button.
2. The shortened URL will be displayed below the text box.
3. Click on the shortened URL to visit the original URL.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
















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
