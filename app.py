import random
import sqlite3
from flask import Flask, redirect, render_template, request, jsonify

app = Flask(__name__, template_folder='templates')

def get_db_connection():
    db = sqlite3.connect('data.db')
    db.row_factory = sqlite3.Row
    return db

def randomString(cursor, length=6):
    letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    while True:
        result_str = ''.join(random.choice(letters) for _ in range(length))
        cursor.execute('SELECT shorturl FROM urls WHERE shorturl = ?', (result_str,))
        if not cursor.fetchone():
            return result_str

@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY, longurl TEXT, shorturl TEXT UNIQUE)')
    cursor.execute('SELECT id, longurl, shorturl FROM urls')
    all_urls = cursor.fetchall()
    urls_list = [{"id": row[0], "longurl": row[1], "shorturl": row[2], "access_url": f"{request.host_url}{row[2]}"} for row in all_urls]

    if request.method == 'POST':
        longurl = request.form.get('longurl')
        if not longurl:
            db.close()
            return render_template('index.html', error='Please enter a URL', all_urls=urls_list)

        cursor.execute('SELECT shorturl FROM urls WHERE longurl = ?', (longurl,))
        result = cursor.fetchone()

        if result:
            db.close()
            return render_template('index.html', host=request.host_url, shorturl=result[0], all_urls=urls_list)
        else:
            shorturl_code = randomString(cursor)
            cursor.execute('INSERT INTO urls (longurl, shorturl) VALUES (?, ?)', (longurl, shorturl_code))
            db.commit()
            db.close()
            return render_template('index.html', host=request.host_url, shorturl=shorturl_code, all_urls=urls_list)

    db.close()
    return render_template('index.html', all_urls=urls_list)

@app.route('/delete/<int:url_id>', methods=['POST'])
def delete_url(url_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('DELETE FROM urls WHERE id = ?', (url_id,))
    db.commit()
    db.close()
    return redirect('/')

@app.route('/<shorturl>')
def redirect_shorturl(shorturl):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('SELECT longurl FROM urls WHERE shorturl = ?', (shorturl,))
    result = cursor.fetchone()
    db.close()

    if result:
        return redirect(result[0])
    else:
        return "URL does not exist"

@app.route('/api/urls', methods=['POST'])
def api_create_url():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()
    longurl = data.get('longurl')

    if not longurl:
        return jsonify({"error": "Missing longurl"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY, longurl TEXT, shorturl TEXT UNIQUE)')
    cursor.execute('SELECT id, shorturl FROM urls WHERE longurl = ?', (longurl,))
    existing = cursor.fetchone()

    if existing:
        db.close()
        return jsonify({
            "id": existing[0],
            "longurl": longurl,
            "shorturl": existing[1],
            "access_url": f"{request.host_url}{existing[1]}",
            "message": "URL already exists"
        }), 200

    shorturl_code = randomString(cursor)
    try:
        cursor.execute('INSERT INTO urls (longurl, shorturl) VALUES (?, ?)', (longurl, shorturl_code))
        db.commit()
        new_id = cursor.lastrowid
        db.close()
        return jsonify({
            "id": new_id,
            "longurl": longurl,
            "shorturl": shorturl_code,
            "access_url": f"{request.host_url}{shorturl_code}"
        }), 201
    except sqlite3.IntegrityError:
        db.close()
        return jsonify({"error": "Failed to create short URL due to collision"}), 500

@app.route('/api/urls', methods=['GET'])
def api_get_urls():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('SELECT id, longurl, shorturl FROM urls')
    urls_list = [{"id": row[0], "longurl": row[1], "shorturl": row[2], "access_url": f"{request.host_url}{row[2]}"} for row in cursor.fetchall()]
    db.close()
    return jsonify(urls_list), 200

@app.route('/api/urls/<int:url_id>', methods=['GET'])
def api_get_url(url_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('SELECT id, longurl, shorturl FROM urls WHERE id = ?', (url_id,))
    row = cursor.fetchone()
    db.close()
    if row:
        return jsonify({"id": row[0], "longurl": row[1], "shorturl": row[2], "access_url": f"{request.host_url}{row[2]}"}), 200
    else:
        return jsonify({"error": "URL not found"}), 404

@app.route('/api/urls/<int:url_id>', methods=['PUT'])
def api_update_url(url_id):
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()
    new_longurl = data.get('longurl')

    if not new_longurl:
        return jsonify({"error": "Missing longurl"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM urls WHERE id = ?', (url_id,))
    if not cursor.fetchone():
        db.close()
        return jsonify({"error": "URL not found"}), 404

    cursor.execute('UPDATE urls SET longurl = ? WHERE id = ?', (new_longurl, url_id))
    db.commit()

    cursor.execute('SELECT id, longurl, shorturl FROM urls WHERE id = ?', (url_id,))
    updated_row = cursor.fetchone()
    db.close()

    return jsonify({"id": updated_row[0], "longurl": updated_row[1], "shorturl": updated_row[2], "access_url": f"{request.host_url}{updated_row[2]}"}), 200

@app.route('/api/urls/<int:url_id>', methods=['DELETE'])
def api_delete_url(url_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM urls WHERE id = ?', (url_id,))
    if not cursor.fetchone():
        db.close()
        return jsonify({"error": "URL not found"}), 404

    cursor.execute('DELETE FROM urls WHERE id = ?', (url_id,))
    db.commit()
    db.close()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
