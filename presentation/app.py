
from flask import Flask, request, render_template_string, jsonify
import requests
import os

app = Flask(__name__)
WORKFLOW_URL = os.getenv('WORKFLOW_URL', 'http://workflow-service:5001')

HTML_FORM = '''
<!DOCTYPE html>
<html>
<head><title>Poster Submission</title></head>
<body>
    <h2>Submit Event Poster</h2>
    <form action="/submit" method="post">
        Title: <input type="text" name="title" required><br>
        Description: <textarea name="description" required></textarea><br>
        Filename: <input type="text" name="filename" required><br>
        <input type="submit" value="Submit">
    </form>
    <hr>
    <h2>Check Result</h2>
    <form action="/result" method="get">
        Record ID: <input type="text" name="id"><br>
        <input type="submit" value="Check">
    </form>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML_FORM

@app.route('/submit', methods=['POST'])
def submit():
    data = {
        'title': request.form['title'],
        'description': request.form['description'],
        'filename': request.form['filename']
    }
    resp = requests.post(f'{WORKFLOW_URL}/submit', json=data)
    return f"Submitted! Your Record ID: {resp.json()['record_id']}"

@app.route('/result', methods=['GET'])
def result():
    record_id = request.args.get('id')
    if not record_id:
        return "Missing ID", 400
    resp = requests.get(f'{WORKFLOW_URL}/result/{record_id}')
    if resp.status_code == 200:
        data = resp.json()
        return f"""
        <h3>Result for Record {record_id}</h3>
        <p>Title: {data['title']}</p>
        <p>Status: <b>{data['status']}</b></p>
        <p>Note: {data['note']}</p>
        <a href='/'>Back</a>
        """
    return "Not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)