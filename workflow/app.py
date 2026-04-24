from flask import Flask, request, jsonify
import requests
import boto3
import json
import os

app = Flask(__name__)

DATA_SERVICE_URL = os.getenv('DATA_SERVICE_URL', 'http://data-service:5002')
LAMBDA_FUNCTION_NAME = os.getenv('LAMBDA_FUNCTION_NAME', 'submission-event')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json

    # 1. 存到 data service
    resp = requests.post(f'{DATA_SERVICE_URL}/submit', json=data)
    if resp.status_code != 200:
        return jsonify({'error': 'Data service failed'}), 500
    record_id = resp.json()['record_id']

    # 2. 触发 Lambda（异步）
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType='Event',
        Payload=json.dumps({'data': data, 'record_id': record_id})
    )

    return jsonify({'record_id': record_id, 'status': 'processing'})

@app.route('/result/<int:record_id>', methods=['GET'])
def result(record_id):
    resp = requests.get(f'{DATA_SERVICE_URL}/result/{record_id}')
    return jsonify(resp.json()), resp.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)