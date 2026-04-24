import json
import boto3
import os
import sqlite3
from datetime import datetime

# 数据库路径（后续会改成容器里的数据库，暂时本地测试用）
DB_PATH = '/tmp/submissions.db'

def lambda_handler(event, context):
    """Submission Event Function: 创建初始记录并触发处理"""
    data = event.get('data', {})
    
    # 1. 存入数据库
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO submissions (title, description, filename, status, note)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data.get('title', ''),
        data.get('description', ''),
        data.get('filename', ''),
        'PENDING',
        'Submission received, processing...'
    ))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    
    # 2. 异步触发 Processing Function
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName=os.environ.get('PROCESSING_FUNCTION_NAME', 'mini-project-processing'),
        InvocationType='Event',
        Payload=json.dumps({'record_id': record_id})
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'record_id': record_id, 'status': 'PENDING'})
    }

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