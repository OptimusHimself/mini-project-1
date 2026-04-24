from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

DATA_SERVICE_URL = os.getenv('DATA_SERVICE_URL', 'http://data-service:5002')
SUBMISSION_FUNCTION_URL = os.getenv('SUBMISSION_FUNCTION_URL', 'https://submissfunction-toofmywica.cn-hangzhou.fcapp.run')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    
    # 校验必填字段
    if not data or not data.get('title') or not data.get('description') or not data.get('filename'):
        return jsonify({'error': 'Missing required fields: title, description, filename'}), 400
    
    # 1. 存到 data service
    try:
        resp = requests.post(f'{DATA_SERVICE_URL}/submit', json=data, timeout=10)
        if resp.status_code != 200:
            return jsonify({'error': 'Data service failed'}), 500
        record_id = resp.json()['record_id']
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Data service error: {str(e)}'}), 500
    
    # 2. 调用阿里云 submission-event 函数（同步）
    try:
        lambda_payload = {
            'record_id': record_id,
            'data': data
        }
        resp = requests.post(
            SUBMISSION_FUNCTION_URL,
            json=lambda_payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        # 记录调用结果（用于调试）
        print(f"Lambda invoked. Status: {resp.status_code}, Response: {resp.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"Lambda timeout for record_id {record_id}")
        # 超时也不影响返回，后台可能仍在处理
    except requests.exceptions.RequestException as e:
        print(f"Lambda invocation failed: {e}")
        # 调用失败也不影响返回，记录日志即可
    
    return jsonify({'record_id': record_id, 'status': 'processing'})

@app.route('/result/<int:record_id>', methods=['GET'])
def result(record_id):
    try:
        resp = requests.get(f'{DATA_SERVICE_URL}/result/{record_id}', timeout=10)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Data service error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)