import json
import boto3
import os
import sqlite3

def lambda_handler(event, context):
    """Processing Function: 应用规则计算状态"""
    record_id = event.get('record_id')
    if not record_id:
        return {'statusCode': 400, 'body': 'Missing record_id'}
    
    # 1. 读取记录
    conn = sqlite3.connect('/tmp/submissions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT title, description, filename FROM submissions WHERE id = ?', (record_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {'statusCode': 404, 'body': 'Record not found'}
    
    title, description, filename = row
    
    # 2. 应用规则
    if not title or not description or not filename:
        final_status = 'INCOMPLETE'
        note = 'Missing required fields'
    elif len(description) < 30:
        final_status = 'NEEDS_REVISION'
        note = f'Description too short ({len(description)}/30 characters)'
    elif not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        final_status = 'NEEDS_REVISION'
        note = 'Invalid file format. Must be .jpg, .jpeg, or .png'
    else:
        final_status = 'READY'
        note = 'All checks passed. Poster is ready.'
    
    # 3. 触发 Result Update Function
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName=os.environ.get('RESULT_UPDATE_FUNCTION_NAME', 'mini-project-result-update'),
        InvocationType='Event',
        Payload=json.dumps({
            'record_id': record_id,
            'status': final_status,
            'note': note
        })
    )
    
    return {'statusCode': 200, 'body': json.dumps({'record_id': record_id, 'status': final_status})}