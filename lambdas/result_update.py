import json
import sqlite3

def lambda_handler(event, context):
    """Result Update Function: 更新数据库中的结果"""
    record_id = event.get('record_id')
    status = event.get('status')
    note = event.get('note')
    
    if not record_id or not status:
        return {'statusCode': 400, 'body': 'Missing record_id or status'}
    
    conn = sqlite3.connect('/tmp/submissions.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE submissions 
        SET status = ?, note = ?
        WHERE id = ?
    ''', (status, note, record_id))
    conn.commit()
    conn.close()
    
    return {
        'statusCode': 200,
        'body': json.dumps({'record_id': record_id, 'status': status, 'updated': True})
    }