
import json
import sqlite3
import os

# 模拟不调用 boto3 的测试
def test_submission_logic():
    data = {
        'title': 'Test Poster',
        'description': 'This is a very long description that exceeds thirty characters easily',
        'filename': 'poster.jpg'
    }
    
    # 模拟数据库操作
    conn = sqlite3.connect('/tmp/test.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            filename TEXT,
            status TEXT,
            note TEXT
        )
    ''')
    cursor.execute('''
        INSERT INTO submissions (title, description, filename, status, note)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['title'], data['description'], data['filename'], 'PENDING', 'Testing'))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    
    print(f"✅ Created record with id: {record_id}")
    return record_id

if __name__ == '__main__':
    test_submission_logic()
