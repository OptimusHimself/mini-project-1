from flask import Flask, request, render_template_string, jsonify
import requests
import os

app = Flask(__name__)
WORKFLOW_URL = os.getenv('WORKFLOW_URL', 'http://workflow-service:5001')

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Poster Submission Portal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #0f0c29;
            background: linear-gradient(145deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        /* Header */
        .header {
            text-align: center;
            margin-bottom: 32px;
        }
        
        .header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.5px;
            text-shadow: 0 4px 20px rgba(0,0,0,0.3);
            margin-bottom: 8px;
        }
        
        .header p {
            color: rgba(255,255,255,0.8);
            font-size: 1rem;
        }
        
        /* Cards */
        .card {
            background: rgba(255,255,255,0.98);
            backdrop-filter: blur(0px);
            border-radius: 28px;
            padding: 36px;
            margin-bottom: 28px;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.4);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 30px 60px -12px rgba(0,0,0,0.5);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 28px;
            border-bottom: 2px solid #eef2ff;
            padding-bottom: 16px;
        }
        
        .card-header .emoji {
            font-size: 32px;
        }
        
        .card-header h2 {
            color: #1e1b4b;
            font-size: 1.6rem;
            font-weight: 700;
            margin: 0;
        }
        
        /* Form */
        .form-group {
            margin-bottom: 24px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2d3a5e;
            font-size: 0.9rem;
            letter-spacing: 0.3px;
        }
        
        label .required {
            color: #ef4444;
            margin-left: 4px;
        }
        
        input[type="text"],
        textarea,
        input[type="file"] {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 16px;
            font-size: 15px;
            transition: all 0.2s;
            background: white;
            font-family: inherit;
        }
        
        input[type="text"]:focus,
        textarea:focus,
        input[type="file"]:focus {
            outline: none;
            border-color: #8b5cf6;
            box-shadow: 0 0 0 3px rgba(139,92,246,0.15);
        }
        
        textarea {
            resize: vertical;
            min-height: 110px;
        }
        
        .file-info {
            margin-top: 10px;
            font-size: 13px;
            color: #6c757d;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .file-info .badge {
            background: #eef2ff;
            padding: 4px 12px;
            border-radius: 30px;
            color: #4f46e5;
            font-weight: 500;
        }
        
        /* Buttons */
        button {
            background: linear-gradient(95deg, #7c3aed 0%, #a78bfa 100%);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 40px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 100%;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 14px 0 rgba(124, 58, 237, 0.4);
        }
        
        button:hover {
            transform: scale(1.01);
            background: linear-gradient(95deg, #6d28d9 0%, #8b5cf6 100%);
            box-shadow: 0 6px 20px rgba(124, 58, 237, 0.6);
        }
        
        /* Result cards */
        .result-card {
            background: #f8fafc;
            border-radius: 20px;
            padding: 20px;
            margin-top: 28px;
            border-left: 6px solid #8b5cf6;
        }
        
        .alert {
            padding: 16px 20px;
            border-radius: 20px;
            margin-bottom: 0;
        }
        
        .alert-error {
            background: #fef2f2;
            color: #b91c1c;
            border: 1px solid #fecaca;
        }
        
        .alert-success {
            background: #ecfdf5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }
        
        .status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 16px;
            border-radius: 40px;
            font-weight: 700;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-ready { background: #d1fae5; color: #065f46; }
        .status-needs { background: #fed7aa; color: #9a3412; }
        .status-incomplete { background: #fee2e2; color: #991b1b; }
        .status-pending { background: #e0e7ff; color: #3730a3; }
        
        .record-id-badge {
            font-size: 2.2rem;
            font-weight: 800;
            color: #7c3aed;
            background: #ede9fe;
            display: inline-block;
            padding: 4px 18px;
            border-radius: 60px;
            margin: 10px 0;
            letter-spacing: 1px;
        }
        
        .btn-link {
            background: none;
            background-color: #f3f4f6;
            color: #4f46e5;
            box-shadow: none;
            font-weight: 600;
            padding: 8px 16px;
            width: auto;
            margin-top: 12px;
            font-size: 0.85rem;
        }
        
        .btn-link:hover {
            background-color: #e0e7ff;
            transform: none;
            box-shadow: none;
        }
        
        .info-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 12px;
        }
        
        .info-item {
            background: white;
            padding: 8px 14px;
            border-radius: 40px;
            font-size: 0.85rem;
            border: 1px solid #e2e8f0;
        }
        
        hr {
            margin: 20px 0;
            border: none;
            border-top: 1px solid #ddd;
        }
        
        @media (max-width: 640px) {
            .card { padding: 24px; }
            .container { padding: 0 12px; }
            .header h1 { font-size: 1.8rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Creator Cloud Studio</h1>
            <p>Submit & validate event posters automatically</p>
        </div>

        <!-- Submit Card -->
        <div class="card">
            <div class="card-header">
                <span class="emoji">📤</span>
                <h2>Submit New Poster</h2>
            </div>
            <form id="submitForm">
                <div class="form-group">
                    <label>Event Title <span class="required">*</span></label>
                    <input type="text" name="title" placeholder="e.g., Spring Music Festival 2026" required>
                </div>
                <div class="form-group">
                    <label>Description <span class="required">*</span></label>
                    <textarea name="description" placeholder="Describe your event in detail (at least 30 characters)"></textarea>
                </div>
                <div class="form-group">
                    <label>Poster File <span class="required">*</span></label>
                    <input type="file" id="posterImage" accept=".jpg,.jpeg,.png">
                    <div class="file-info">
                        <span>📎</span>
                        <span id="fileInfo" class="badge">No file chosen</span>
                    </div>
                </div>
                <button type="submit">✨ Submit for Review</button>
            </form>
            <div id="submitResult"></div>
        </div>

        <!-- Query Card -->
        <div class="card">
            <div class="card-header">
                <span class="emoji">🔎</span>
                <h2>Check Submission Status</h2>
            </div>
            <form id="queryForm">
                <div class="form-group">
                    <label>Record ID</label>
                    <input type="text" name="record_id" placeholder="e.g., 42">
                </div>
                <button type="submit">📋 Check Status</button>
            </form>
            <div id="queryResult"></div>
        </div>
    </div>

    <script>
        const workflowUrl = '{{ workflow_url }}';
        
        // Submit handler – no frontend validation blocking
        document.getElementById('submitForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = e.target.title.value;
            const description = e.target.description.value;
            const fileInput = document.getElementById('posterImage');
            const filename = fileInput.files.length > 0 ? fileInput.files[0].name : '';
            
            // Remove frontend blocking validation
            // All data (even empty/invalid) goes to backend, lambda decides status.
            
            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, description, filename })
                });
                const data = await response.json();
                if (response.ok) {
                    showResult('submitResult', 'success', 
                        `✅ <strong>Submitted successfully!</strong><br>
                        Your Record ID: <div class="record-id-badge">${data.record_id}</div>
                        <button class="btn-link" onclick="autoQueryRecord('${data.record_id}')">🔍 Check Status Now</button>`
                    );
                    document.getElementById('submitForm').reset();
                    document.getElementById('fileInfo').innerHTML = 'No file chosen';
                } else {
                    showResult('submitResult', 'error', data.error || 'Submission failed');
                }
            } catch (err) {
                showResult('submitResult', 'error', '⚠️ Network error. Is the backend running?');
            }
        });
        
        // Query handler
        document.getElementById('queryForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const recordId = e.target.record_id.value;
            if (!recordId) {
                showResult('queryResult', 'error', 'Please enter a Record ID');
                return;
            }
            
            try {
                const response = await fetch(`/result?id=${recordId}`);
                if (response.ok) {
                    const data = await response.json();
                    let statusClass = 'status-pending';
                    let statusText = data.status || 'PENDING';
                    if (data.status === 'READY') statusClass = 'status-ready';
                    else if (data.status === 'NEEDS_REVISION') statusClass = 'status-needs';
                    else if (data.status === 'INCOMPLETE') statusClass = 'status-incomplete';
                    
                    showResult('queryResult', 'success',
                        `<div style="margin-bottom: 16px;">
                            <strong>🎯 Record #${recordId}</strong>
                        </div>
                        <div class="info-grid">
                            <div class="info-item"><strong>Title:</strong> ${escapeHtml(data.title || '—')}</div>
                            <div class="info-item"><strong>Filename:</strong> ${escapeHtml(data.filename || '—')}</div>
                        </div>
                        <p><strong>Description:</strong><br>${escapeHtml(data.description || '—')}</p>
                        <p><strong>Status:</strong> <span class="status ${statusClass}">${escapeHtml(statusText)}</span></p>
                        <p><strong>Note:</strong> ${escapeHtml(data.note || 'Processing...')}</p>`
                    );
                } else if (response.status === 404) {
                    showResult('queryResult', 'error', 'Record not found. Double-check the ID.');
                } else {
                    showResult('queryResult', 'error', 'Failed to fetch result.');
                }
            } catch (err) {
                showResult('queryResult', 'error', 'Network error while querying.');
            }
        });
        
        function autoQueryRecord(recordId) {
            const queryInput = document.querySelector('[name="record_id"]');
            if (queryInput) {
                queryInput.value = recordId;
                document.getElementById('queryForm').querySelector('button').click();
            }
        }
        
        function showResult(containerId, type, html) {
            const container = document.getElementById(containerId);
            const alertClass = type === 'error' ? 'alert-error' : 'alert-success';
            container.innerHTML = `<div class="result-card"><div class="alert ${alertClass}">${html}</div></div>`;
            setTimeout(() => {
                if (type === 'success' && containerId === 'submitResult') {
                    // persist for better UX
                }
            }, 8000);
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
        
        document.getElementById('posterImage').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('fileInfo').innerHTML = `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            } else {
                document.getElementById('fileInfo').innerHTML = 'No file chosen';
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
        
        # No blocking validation — allow empty/incomplete data
        # All records are saved, lambda decides status
        
        resp = requests.post(f'{WORKFLOW_URL}/submit', json={
            'title': title,
            'description': description,
            'filename': filename
        }, timeout=30)
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