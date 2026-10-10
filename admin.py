#!/usr/bin/env python3
"""APK Store Admin Panel — Local Flask server"""

from flask import Flask, request, jsonify, render_template_string, session
import os, json, secrets, shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

BASE = os.path.dirname(os.path.abspath(__file__))
APKS_DIR = os.path.join(BASE, 'apks')
DATA_FILE = os.path.join(BASE, 'apks.json')
PASSWORD = "admin@123"   # ← YAHAN APNA PASSWORD SET KARO

os.makedirs(APKS_DIR, exist_ok=True)

# ============ DATA HELPERS ============
def load_apks():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except: return []
    return []

def save_apks(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def file_size_mb(path):
    try:
        return f"{os.path.getsize(path) / 1024 / 1024:.1f} MB"
    except: return "?"

# ============ ADMIN UI ============
ADMIN_HTML = r'''<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin · APK Store</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system,sans-serif;-webkit-tap-highlight-color:transparent}
body{background:linear-gradient(135deg,#0a0e1a,#0f1422);color:#e8eaf2;min-height:100vh;padding:16px;-webkit-font-smoothing:antialiased}
.container{max-width:600px;margin:0 auto}

/* HEADER */
.header{background:linear-gradient(135deg,#1a2035,#0f1422);border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:16px 20px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 8px 24px rgba(0,0,0,.4)}
.header h1{font-size:1.1rem;font-weight:900;color:#fff}
.header .sub{font-size:.65rem;color:rgba(255,255,255,.4);font-weight:700;letter-spacing:.15em;text-transform:uppercase;margin-top:2px}
.header .count{background:linear-gradient(135deg,#ef4444,#b91c1c);color:#fff;padding:6px 12px;border-radius:20px;font-size:.75rem;font-weight:900}

/* CARD */
.card{background:linear-gradient(180deg,rgba(24,30,52,.85),rgba(15,20,35,.85));border:1px solid rgba(255,255,255,.07);border-radius:18px;padding:20px;margin-bottom:14px;box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 8px 24px -12px rgba(0,0,0,.6)}
.card-title{font-size:.68rem;color:rgba(255,255,255,.4);font-weight:800;letter-spacing:.18em;text-transform:uppercase;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.card-title::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(255,255,255,.08),transparent)}

/* FORM */
label{display:block;font-size:.7rem;color:rgba(255,255,255,.5);font-weight:800;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;margin-top:12px}
label:first-of-type{margin-top:0}
input,select,textarea{width:100%;padding:12px 14px;background:rgba(255,255,255,.03);border:1.5px solid rgba(255,255,255,.08);border-radius:12px;color:#fff;font-family:inherit;font-size:.9rem;outline:none;transition:.2s}
input:focus,select:focus,textarea:focus{border-color:rgba(239,68,68,.5);background:rgba(255,255,255,.05)}
input::placeholder,textarea::placeholder{color:rgba(255,255,255,.25)}
select option{background:#1a2035;color:#fff}

.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:450px){.row{grid-template-columns:1fr}}

.file-input{position:relative}
.file-input input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer;z-index:2}
.file-display{padding:14px 16px;background:rgba(255,255,255,.03);border:1.5px dashed rgba(255,255,255,.15);border-radius:12px;text-align:center;font-size:.85rem;color:rgba(255,255,255,.5);transition:.2s}
.file-input:hover .file-display{border-color:rgba(239,68,68,.5);color:#fff}
.file-display.has{background:rgba(74,222,128,.05);border:1.5px solid rgba(74,222,128,.4);color:#4ade80}
.file-display b{color:#fff}

/* EMOJI PICKER */
.emoji-grid{display:grid;grid-template-columns:repeat(8,1fr);gap:6px;margin-top:6px}
.emoji-opt{padding:8px;background:rgba(255,255,255,.03);border:1.5px solid rgba(255,255,255,.08);border-radius:10px;font-size:1.2rem;cursor:pointer;text-align:center;transition:.15s;line-height:1}
.emoji-opt:hover{background:rgba(255,255,255,.08);transform:scale(1.05)}
.emoji-opt.sel{background:rgba(239,68,68,.15);border-color:#ef4444;box-shadow:0 0 0 2px rgba(239,68,68,.3)}
@media(max-width:450px){.emoji-grid{grid-template-columns:repeat(6,1fr)}}

/* BUTTONS */
.btn{padding:14px 20px;border-radius:12px;border:none;font-family:inherit;font-size:.9rem;font-weight:800;cursor:pointer;transition:.2s;letter-spacing:.02em}
.btn-primary{background:linear-gradient(135deg,#4ade80,#22c55e);color:#0a0e1a;box-shadow:0 6px 20px rgba(74,222,128,.35)}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 26px rgba(74,222,128,.5)}
.btn-primary:active{transform:scale(.98)}
.btn-primary:disabled{opacity:.4;cursor:not-allowed;transform:none}
.btn-danger{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3);padding:8px 14px;font-size:.75rem}
.btn-danger:hover{background:rgba(239,68,68,.25)}
.btn-sm{padding:8px 14px;font-size:.75rem}
.full{width:100%}

/* APK LIST */
.apk-item{display:flex;align-items:center;gap:12px;padding:12px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:12px;margin-bottom:8px}
.apk-item .icon{width:44px;height:44px;border-radius:11px;background:linear-gradient(135deg,#1a2035,#2a3050);display:flex;align-items:center;justify-content:center;font-size:1.5rem;flex-shrink:0}
.apk-item .info{flex:1;min-width:0}
.apk-item .name{font-weight:800;font-size:.88rem;color:#fff;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.apk-item .meta{font-size:.68rem;color:rgba(255,255,255,.4);font-weight:600}
.apk-item .actions{display:flex;gap:6px;flex-shrink:0}

/* TOAST */
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(100px);background:rgba(20,26,44,.95);border:1px solid rgba(255,255,255,.1);padding:12px 22px;border-radius:14px;font-size:.85rem;font-weight:700;backdrop-filter:blur(20px);z-index:9999;transition:.3s;pointer-events:none;max-width:90vw;text-align:center}
.toast.show{transform:translateX(-50%) translateY(0)}
.toast.ok{border-color:rgba(74,222,128,.4);color:#4ade80}
.toast.err{border-color:rgba(239,68,68,.4);color:#f87171}

/* LOGIN */
.login-card{max-width:380px;margin:80px auto;background:linear-gradient(180deg,rgba(24,30,52,.95),rgba(15,20,35,.95));border:1px solid rgba(255,255,255,.08);border-radius:22px;padding:32px 24px;text-align:center;box-shadow:0 30px 80px rgba(0,0,0,.6)}
.login-card .lock{width:70px;height:70px;border-radius:18px;background:linear-gradient(135deg,#ef4444,#b91c1c);margin:0 auto 18px;display:flex;align-items:center;justify-content:center;font-size:2rem;box-shadow:0 8px 24px rgba(239,68,68,.4)}
.login-card h2{font-size:1.3rem;font-weight:900;color:#fff;margin-bottom:6px}
.login-card p{font-size:.82rem;color:rgba(255,255,255,.5);margin-bottom:24px}

.empty{text-align:center;padding:24px;color:rgba(255,255,255,.3);font-size:.85rem}
</style>
</head>
<body>
<div class="container" id="app"></div>
<div class="toast" id="toast"></div>

<script>
let APKS = [];
let selectedEmoji = '📱';
let editingId = null;
let selectedFile = null;

const EMOJIS = ['📱','🔒','📥','🎨','🎵','💬','🎮','📷','🎬','📚','💼','🏦','🛒','🚗','🌐','⚡','🔧','🎯','💡','🎁','📊','🎧','⏰','🗺️'];

async function loadData(){
  const r = await fetch('/api/apks');
  APKS = await r.json();
  renderApp();
}

function renderApp(){
  document.getElementById('app').innerHTML = `
    <div class="header">
      <div>
        <h1>🔐 Admin Panel</h1>
        <div class="sub">APK Store Manager</div>
      </div>
      <div class="count">${APKS.length} APKs</div>
    </div>

    <div class="card">
      <div class="card-title">➕ ${editingId ? 'Edit APK' : 'Add New APK'}</div>
      
      <label>App Name</label>
      <input type="text" id="f_name" placeholder="e.g. VPN Pro" value="${editingId ? APKS.find(a => a.id === editingId)?.name || '' : ''}">

      <div class="row">
        <div>
          <label>Category</label>
          <select id="f_cat">
            <option value="Tools">Tools</option>
            <option value="Games">Games</option>
            <option value="Photography">Photography</option>
            <option value="Music">Music</option>
            <option value="Communication">Communication</option>
            <option value="Downloader">Downloader</option>
            <option value="Finance">Finance</option>
            <option value="Education">Education</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div>
          <label>Version</label>
          <input type="text" id="f_ver" placeholder="1.0.0" value="${editingId ? APKS.find(a => a.id === editingId)?.version || '' : ''}">
        </div>
      </div>

      <label>Icon (emoji select karo)</label>
      <div class="emoji-grid" id="emojiGrid">
        ${EMOJIS.map(e => `<div class="emoji-opt" onclick="pickEmoji('${e}')" data-e="${e}">${e}</div>`).join('')}
      </div>

      <label>APK File</label>
      <div class="file-input">
        <input type="file" id="f_file" accept=".apk" onchange="handleFile(this)">
        <div class="file-display" id="fileDisplay">
          ${editingId ? '🔄 Nayi file select karo (ya same rakho)' : '📁 Tap karke APK select karo'}
        </div>
      </div>

      <div style="margin-top:18px;display:flex;gap:10px">
        <button class="btn btn-primary full" onclick="saveAPK()" id="saveBtn">
          ${editingId ? '💾 Update APK' : '➕ Add APK'}
        </button>
        ${editingId ? '<button class="btn btn-danger btn-sm" onclick="cancelEdit()" style="padding:14px 18px">✕</button>' : ''}
      </div>
    </div>

    <div class="card">
      <div class="card-title">📦 Installed APKs</div>
      ${APKS.length === 0 ? '<div class="empty">Koi APK nahi. Upar se add karo.</div>' : 
        APKS.map(a => `
          <div class="apk-item">
            <div class="icon">${a.icon}</div>
            <div class="info">
              <div class="name">${a.name}</div>
              <div class="meta">v${a.version} · ${a.size} · ${a.category}</div>
            </div>
            <div class="actions">
              <button class="btn btn-danger btn-sm" onclick="editAPK('${a.id}')">✏️</button>
              <button class="btn btn-danger btn-sm" onclick="deleteAPK('${a.id}')">🗑</button>
            </div>
          </div>
        `).join('')
      }
    </div>

    <div class="card">
      <div class="card-title">🚀 Deploy</div>
      <p style="font-size:.82rem;color:rgba(255,255,255,.5);line-height:1.6;margin-bottom:12px">
        APKs add karne ke baad, Termux me ye commands chalao:
      </p>
      <div style="background:#0a0e1a;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:12px;font-family:monospace;font-size:.75rem;color:#4ade80;line-height:1.7">
        cd ~/apk-store<br>
        git add .<br>
        git commit -m "Update APKs"<br>
        git push
      </div>
    </div>
  `;
  
  if(editingId){
    const a = APKS.find(x => x.id === editingId);
    if(a) {
      document.getElementById('f_cat').value = a.category;
      selectedEmoji = a.icon;
    }
  }
  updateEmojiSelection();
}

function pickEmoji(e){
  selectedEmoji = e;
  updateEmojiSelection();
}

function updateEmojiSelection(){
  document.querySelectorAll('.emoji-opt').forEach(el => {
    el.classList.toggle('sel', el.dataset.e === selectedEmoji);
  });
}

function handleFile(input){
  const file = input.files[0];
  if(!file) return;
  selectedFile = file;
  const sizeMB = (file.size / 1024 / 1024).toFixed(1);
  const display = document.getElementById('fileDisplay');
  display.classList.add('has');
  display.innerHTML = `✅ <b>${file.name}</b> (${sizeMB} MB)`;
}

async function saveAPK(){
  const name = document.getElementById('f_name').value.trim();
  const cat = document.getElementById('f_cat').value;
  const ver = document.getElementById('f_ver').value.trim() || '1.0';
  
  if(!name){ toast('App name daalo', 'err'); return; }
  
  if(!editingId && !selectedFile){
    toast('APK file select karo', 'err'); return;
  }
  
  const fd = new FormData();
  fd.append('name', name);
  fd.append('category', cat);
  fd.append('version', ver);
  fd.append('icon', selectedEmoji);
  if(selectedFile) fd.append('file', selectedFile);
  if(editingId) fd.append('id', editingId);
  
  document.getElementById('saveBtn').disabled = true;
  document.getElementById('saveBtn').textContent = 'Uploading...';
  
  try {
    const r = await fetch('/api/save', { method:'POST', body: fd });
    const d = await r.json();
    if(d.ok){
      toast(editingId ? 'APK updated!' : 'APK added!', 'ok');
      resetForm();
      await loadData();
    } else {
      toast(d.error || 'Error', 'err');
    }
  } catch(e){
    toast('Upload failed: ' + e.message, 'err');
  }
  
  document.getElementById('saveBtn').disabled = false;
}

function resetForm(){
  editingId = null;
  selectedFile = null;
  selectedEmoji = '📱';
  renderApp();
}

function cancelEdit(){
  resetForm();
}

function editAPK(id){
  editingId = id;
  const a = APKS.find(x => x.id === id);
  if(a) selectedEmoji = a.icon;
  renderApp();
  window.scrollTo({top:0, behavior:'smooth'});
}

async function deleteAPK(id){
  if(!confirm('Ye APK delete karna hai?')) return;
  const r = await fetch('/api/delete?id=' + id, { method:'DELETE' });
  const d = await r.json();
  if(d.ok){
    toast('APK deleted', 'ok');
    await loadData();
  } else {
    toast(d.error, 'err');
  }
}

let toastTimer;
function toast(msg, type){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show ' + (type || '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2500);
}

loadData();
</script>
</body>
</html>'''

# ============ ROUTES ============
@app.route('/')
def admin():
    if not session.get('logged_in'):
        return render_template_string(LOGIN_HTML)
    return render_template_string(ADMIN_HTML)

LOGIN_HTML = '''<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login · Admin</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,sans-serif;-webkit-tap-highlight-color:transparent}
body{background:linear-gradient(135deg,#0a0e1a,#0f1422);color:#e8eaf2;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{max-width:380px;width:100%;background:linear-gradient(180deg,rgba(24,30,52,.95),rgba(15,20,35,.95));border:1px solid rgba(255,255,255,.08);border-radius:22px;padding:32px 24px;text-align:center;box-shadow:0 30px 80px rgba(0,0,0,.6)}
.lock{width:70px;height:70px;border-radius:18px;background:linear-gradient(135deg,#ef4444,#b91c1c);margin:0 auto 18px;display:flex;align-items:center;justify-content:center;font-size:2rem;box-shadow:0 8px 24px rgba(239,68,68,.4)}
h2{font-size:1.3rem;font-weight:900;color:#fff;margin-bottom:6px}
p{font-size:.82rem;color:rgba(255,255,255,.5);margin-bottom:24px}
input{width:100%;padding:14px 16px;background:rgba(255,255,255,.03);border:1.5px solid rgba(255,255,255,.08);border-radius:12px;color:#fff;font-family:inherit;font-size:1rem;outline:none;text-align:center;letter-spacing:2px;transition:.2s}
input:focus{border-color:rgba(239,68,68,.5)}
button{width:100%;padding:14px;background:linear-gradient(135deg,#ef4444,#b91c1c);color:#fff;border:none;border-radius:12px;font-family:inherit;font-size:.95rem;font-weight:800;cursor:pointer;margin-top:12px;box-shadow:0 6px 20px rgba(239,68,68,.35);transition:.2s}
button:hover{transform:translateY(-2px)}
button:active{transform:scale(.98)}
.err{color:#f87171;font-size:.8rem;margin-top:10px;min-height:18px}
</style>
</head>
<body>
<div class="card">
  <div class="lock">🔐</div>
  <h2>Admin Login</h2>
  <p>Password daalo</p>
  <form onsubmit="login(event)">
    <input type="password" id="pw" placeholder="••••••••" autofocus>
    <button type="submit">Login</button>
    <div class="err" id="err"></div>
  </form>
</div>
<script>
async function login(e){
  e.preventDefault();
  const pw = document.getElementById('pw').value;
  const r = await fetch('/api/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({password: pw})
  });
  const d = await r.json();
  if(d.ok) window.location.href = '/';
  else document.getElementById('err').textContent = 'Galat password';
}
</script>
</body>
</html>'''

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('password') == PASSWORD:
        session['logged_in'] = True
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 401

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/apks')
def get_apks():
    if not session.get('logged_in'): return jsonify([]), 401
    return jsonify(load_apks())

@app.route('/api/save', methods=['POST'])
def save():
    if not session.get('logged_in'): return jsonify({'ok': False, 'error': 'Login'}), 401
    
    apks = load_apks()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Other')
    version = request.form.get('version', '1.0')
    icon = request.form.get('icon', '📱')
    editing_id = request.form.get('id')
    file = request.files.get('file')
    
    if not name:
        return jsonify({'ok': False, 'error': 'Name required'})
    
    # Edit mode
    if editing_id:
        apk = next((a for a in apks if a['id'] == editing_id), None)
        if not apk:
            return jsonify({'ok': False, 'error': 'APK not found'})
        
        apk['name'] = name
        apk['category'] = category
        apk['version'] = version
        apk['icon'] = icon
        
        # New file uploaded?
        if file and file.filename:
            safe = editing_id + '.apk'
            path = os.path.join(APKS_DIR, safe)
            file.save(path)
            apk['file'] = f'apks/{safe}'
            apk['size'] = file_size_mb(path)
        
        save_apks(apks)
        return jsonify({'ok': True})
    
    # New APK
    if not file or not file.filename:
        return jsonify({'ok': False, 'error': 'APK file required'})
    
    # Generate ID from name
    import re
    apk_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:30]
    base_id = apk_id
    n = 1
    while any(a['id'] == apk_id for a in apks):
        apk_id = f'{base_id}-{n}'
        n += 1
    
    safe = apk_id + '.apk'
    path = os.path.join(APKS_DIR, safe)
    file.save(path)
    
    new_apk = {
        'id': apk_id,
        'name': name,
        'icon': icon,
        'category': category,
        'version': version,
        'size': file_size_mb(path),
        'file': f'apks/{safe}'
    }
    apks.append(new_apk)
    save_apks(apks)
    return jsonify({'ok': True, 'apk': new_apk})

@app.route('/api/delete', methods=['DELETE'])
def delete():
    if not session.get('logged_in'): return jsonify({'ok': False, 'error': 'Login'}), 401
    apk_id = request.args.get('id')
    apks = load_apks()
    apk = next((a for a in apks if a['id'] == apk_id), None)
    if not apk:
        return jsonify({'ok': False, 'error': 'Not found'})
    
    # Delete file
    file_path = os.path.join(BASE, apk['file'])
    if os.path.exists(file_path):
        os.remove(file_path)
    
    apks = [a for a in apks if a['id'] != apk_id]
    save_apks(apks)
    return jsonify({'ok': True})

if __name__ == '__main__':
    # Auto-create apks.json agar nahi hai
    if not os.path.exists(DATA_FILE):
        save_apks([])
    
    print("\n" + "="*55)
    print("🔐 Admin Panel Chalu")
    print("="*55)
    print("📱 Chrome me kholo: http://localhost:5000")
    print(f"🔑 Password: {PASSWORD}")
    print("⚠️  Server band karne ke liye: Ctrl+C")
    print("="*55 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
