from flask import Flask, request, render_template_string, jsonify
import requests
import os
import re

app = Flask(__name__)
WORKFLOW_URL = os.getenv('WORKFLOW_URL', 'http://workflow-service:5001')

# 允许的图片扩展名
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Poster Submission</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 700px;
            margin: 0 auto;
        }
        
        .card {
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 24px;
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #555;
        }
        
        input[type="text"],
        textarea,
        input[type="file"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus,
        textarea:focus,
        input[type="file"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .file-info {
            margin-top: 8px;
            font-size: 12px;
            color: #888;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .result-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .status {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }
        
        .status-ready { background: #d4edda; color: #155724; }
        .status-needs { background: #fff3cd; color: #856404; }
        .status-incomplete { background: #f8d7da; color: #721c24; }
        .status-pending { background: #e2e3e5; color: #383d41; }
        
        .record-id {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        
        .alert {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 16px;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .btn-link {
            background: none;
            color: #667eea;
            text-decoration: underline;
            padding: 0;
            margin-top: 10px;
        }
        
        .btn-link:hover {
            background: none;
            transform: none;
            box-shadow: none;
        }
        
        hr {
            margin: 20px 0;
            border: none;
            border-top: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 提交表单卡片 -->
        <div class="card">
            <h2>📝 提交活动海报</h2>
            <form id="submitForm">
                <div class="form-group">
                    <label>活动标题 *</label>
                    <input type="text" name="title" required placeholder="例如：春季音乐会">
                </div>
                <div class="form-group">
                    <label>活动描述 *</label>
                    <textarea name="description" required placeholder="至少30个字符，详细描述活动内容..."></textarea>
                </div>
                <div class="form-group">
                    <label>海报图片 *</label>
                    <input type="file" id="posterImage" accept=".jpg,.jpeg,.png">
                    <div class="file-info" id="fileInfo">未选择文件</div>
                </div>
                <button type="submit">✨ 提交海报</button>
            </form>
            
            <div id="submitResult"></div>
        </div>
        
        <!-- 查询结果卡片 -->
        <div class="card">
            <h2>🔍 查询审核结果</h2>
            <form id="queryForm">
                <div class="form-group">
                    <label>记录ID</label>
                    <input type="text" name="record_id" placeholder="例如：42">
                </div>
                <button type="submit">📊 查询状态</button>
            </form>
            
            <div id="queryResult"></div>
        </div>
    </div>
    
    <script>
        const workflowUrl = '{{ workflow_url }}';
        
        // 提交表单处理
        document.getElementById('submitForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = e.target.title.value;
            const description = e.target.description.value;
            const fileInput = document.getElementById('posterImage');
            const filename = fileInput.files.length > 0 ? fileInput.files[0].name : '';
            
            // 验证文件名后缀
            const allowedExt = ['.jpg', '.jpeg', '.png'];
            const ext = filename.toLowerCase().slice(filename.lastIndexOf('.'));
            if (!filename || !allowedExt.includes(ext)) {
                showResult('submitResult', 'error', '请选择有效的图片文件 (.jpg, .jpeg, .png)');
                return;
            }
            
            if (description.length < 30) {
                showResult('submitResult', 'error', '描述至少需要30个字符，当前长度：' + description.length);
                return;
            }
            
            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, description, filename })
                });
                const data = await response.json();
                if (response.ok) {
                    showResult('submitResult', 'success', 
                        `✅ 提交成功！<br>你的记录ID：<strong class="record-id">${data.record_id}</strong>
                        <br><button class="btn-link" onclick="document.querySelector('[name=\"record_id\"]').value = '${data.record_id}'; document.getElementById('queryForm').querySelector('button').click();">🔍 立即查看结果</button>`
                    );
                    document.getElementById('submitForm').reset();
                    document.getElementById('fileInfo').innerText = '未选择文件';
                } else {
                    showResult('submitResult', 'error', data.error || '提交失败，请重试');
                }
            } catch (err) {
                showResult('submitResult', 'error', '网络错误，请检查服务是否正常运行');
            }
        });
        
        // 查询表单处理
        document.getElementById('queryForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const recordId = e.target.record_id.value;
            if (!recordId) {
                showResult('queryResult', 'error', '请输入记录ID');
                return;
            }
            
            try {
                const response = await fetch(`/result?id=${recordId}`);
                if (response.ok) {
                    const data = await response.json();
                    let statusClass = 'status-pending';
                    let statusText = data.status;
                    if (data.status === 'READY') statusClass = 'status-ready';
                    else if (data.status === 'NEEDS_REVISION') statusClass = 'status-needs';
                    else if (data.status === 'INCOMPLETE') statusClass = 'status-incomplete';
                    
                    showResult('queryResult', 'success',
                        `<h3>📄 记录 #${recordId}</h3>
                        <p><strong>标题：</strong> ${escapeHtml(data.title)}</p>
                        <p><strong>描述：</strong> ${escapeHtml(data.description)}</p>
                        <p><strong>文件名：</strong> ${escapeHtml(data.filename)}</p>
                        <p><strong>状态：</strong> <span class="status ${statusClass}">${escapeHtml(statusText)}</span></p>
                        <p><strong>说明：</strong> ${escapeHtml(data.note || '处理中...')}</p>`
                    );
                } else if (response.status === 404) {
                    showResult('queryResult', 'error', '未找到该记录，请检查ID是否正确');
                } else {
                    showResult('queryResult', 'error', '查询失败，请重试');
                }
            } catch (err) {
                showResult('queryResult', 'error', '网络错误，请检查服务是否正常运行');
            }
        });
        
        function showResult(containerId, type, html) {
            const container = document.getElementById(containerId);
            const alertClass = type === 'error' ? 'alert-error' : 'alert-success';
            container.innerHTML = `<div class="result-card"><div class="alert ${alertClass}">${html}</div></div>`;
            setTimeout(() => {
                if (type === 'success' && containerId === 'submitResult') {
                    // 保持成功消息，不清空
                } else if (type === 'success') {
                    // 可选：5秒后清空查询结果
                }
            }, 5000);
        }
        
        function escapeHtml(str) {
            if (!str) return '';
            return str.replace(/[&<>]/g, function(m) {
                if (m === '&') return '&amp;';
                if (m === '<') return '&lt;';
                if (m === '>') return '&gt;';
                return m;
            });
        }
        
        // 文件选择显示
        document.getElementById('posterImage').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('fileInfo').innerHTML = `📎 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            } else {
                document.getElementById('fileInfo').innerHTML = '未选择文件';
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE, workflow_url=WORKFLOW_URL)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request, expected JSON'}), 400
        
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        filename = data.get('filename', '').strip()
        
        if not title or not description or not filename:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # 后端额外校验
        if len(description) < 30:
            return jsonify({'error': f'Description must be at least 30 characters (current: {len(description)})'}), 400
        
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'error': f'Invalid file format. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        resp = requests.post(f'{WORKFLOW_URL}/submit', json=data, timeout=30)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Workflow service error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/result', methods=['GET'])
def result():
    try:
        record_id = request.args.get('id')
        if not record_id or not record_id.isdigit():
            return jsonify({'error': 'Invalid record ID'}), 400
        
        resp = requests.get(f'{WORKFLOW_URL}/result/{record_id}', timeout=30)
        if resp.status_code == 404:
            return jsonify({'error': 'Record not found'}), 404
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Workflow service error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)