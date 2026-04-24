from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = '/data/submissions.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            filename TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/submit', methods=['POST'])
def create_submission():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissions (title, description, filename, status, note)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['title'], data['description'], data['filename'], 'PENDING', 'Processing...'))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return jsonify({'record_id': record_id})

@app.route('/result/<int:record_id>', methods=['GET'])
def get_result(record_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT title, description, filename, status, note FROM submissions WHERE id = ?', (record_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({
            'title': row[0], 'description': row[1], 'filename': row[2],
            'status': row[3], 'note': row[4]
        })
    return jsonify({'error': 'Not found'}), 404

@app.route('/update/<int:record_id>', methods=['PUT'])
def update_result(record_id):
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE submissions SET status = ?, note = ? WHERE id = ?', (data['status'], data['note'], record_id))
    conn.commit()
    conn.close()
    return jsonify({'updated': True})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002)