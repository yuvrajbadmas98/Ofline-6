import os, random, string, time, requests
from flask import Flask, request, render_template_string, session
from threading import Thread

app = Flask(__name__)
app.secret_key = 'secret_key_here'

user_sessions, stop_keys = {}, {}

# ───────── HELPERS ─────────
def generate_stop_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))

def read_comments(f):
    return [l.strip() for l in f.read().decode('utf-8').splitlines() if l.strip()]

def read_tokens(f):
    return [l.strip() for l in f.read().decode('utf-8').splitlines() if l.strip()]

# ───────── COMMENT POSTER ─────────
def post_comments(uid):
    d = user_sessions[uid]
    com, toks, pid, spd, tgt, skey = d.values()
    idx = 0
    while True:
        if stop_keys.get(uid) == skey:
            print(f'[{uid}] Stopped by key.')
            break
        if not toks:
            print(f'[{uid}] No tokens, halting.')
            break
        msg   = f"{tgt} {com[idx % len(com)]}"
        token = toks[idx % len(toks)]
        url   = f"https://graph.facebook.com/{pid}/comments"
        try:
            r = requests.post(url, params={'message': msg, 'access_token': token})
            print(f"[{uid}] {'Sent' if r.status_code==200 else r.text}: {msg}")
        except Exception as e:
            print(f"[{uid}] Exception: {e}")
        idx += 1
        # 2 s base +  ±0.3 s jitter  → FB detection से बचने में मदद
        time.sleep(spd + random.uniform(-0.3, 0.3))

# ───────── ROUTES ─────────
@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        act = request.form.get("action")
        if act == "start":
            uid = session.get("uid", str(time.time())); session["uid"] = uid
            pid  = request.form["post_id"]
            spd  = int(request.form["speed"])
            tgt  = request.form["target_name"]
            toks = []
            if request.form.get("single_token"):
                toks.append(request.form["single_token"])
            elif 'token_file' in request.files and request.files['token_file']:
                toks = read_tokens(request.files['token_file'])
            coms = []
            if 'comments_file' in request.files and request.files['comments_file']:
                coms = read_comments(request.files['comments_file'])
            skey = generate_stop_key()
            user_sessions[uid] = dict(post_id=pid,tokens=toks,comments=coms,
                                      target_name=tgt,speed=spd,stop_key=skey)
            stop_keys[uid] = ""
            Thread(target=post_comments, args=(uid,), daemon=True).start()
            message = f"Task started. Stop Key: {skey}"
        elif act == "stop":
            uid = session.get("uid"); key = request.form.get("entered_stop_key","")
            if uid in user_sessions:
                stop_keys[uid] = key; message = "Stop key sent."

    return render_template_string('''
<!DOCTYPE html><html><head>
<title>🙂 𝗚⃪𝗔⃪𝗪⃪𝗡⃪𝗗⃪ 𝗧⃪𝗢⃪𝗗⃪ 𝗣⃪𝗢⃪𝗦⃪𝗧⃪ 𝗦⃪𝗘⃪𝗥⃪𝗩⃪𝗘⃪𝗥⃪ 🙂</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box;font-family:sans-serif}
body{
  margin:0;padding:0;background:url('https://i.ibb.co/MW0CQdQ/2ad93577c9fa0598138cd27ff8ebe151.jpg') center/cover fixed no-repeat;
  color:#fff;display:flex;flex-direction:column;align-items:center;min-height:100vh}
.title{font-size:1.2rem;font-weight:bold;color:#39ff14;margin:20px 0 10px;text-align:center}
.container{
  background:transparent;border:2px solid #fff;border-radius:20px;padding:25px 20px;width:90%;max-width:400px;
  box-shadow:0 0 15px #fff;margin-bottom:20px;text-align:center}
label{font-weight:bold;display:block;margin-top:10px;text-align:left}
input[type=text],input[type=number],input[type=file]{
  width:100%;padding:10px;margin-top:4px;border:2px solid #ff0;border-radius:20px;background:rgba(255,255,255,.1);color:#fff}
.token-btn,.btn{
  margin-top:15px;padding:12px;border:2px solid #ff0;border-radius:20px;font-weight:bold;cursor:pointer;width:100%}
.token-btn{background:rgba(0,0,0,.4);color:#39ff14}
.btn.start{background:#00e600;color:#000}
.btn.stop{background:#ff3333;color:#000}
.stop-section{margin-top:15px}
.message{margin-top:10px;font-size:.95rem;color:#ffcc00}
</style></head><body>
<div class="title">😡 𝗕⃪𝗦⃪𝗗⃪𝗞⃪ 𝗣⃪𝗢⃪𝗦⃪𝗧⃪ 𝗣⃪𝗬⃪ 𝗧⃪𝗔⃪𝗧⃪𝗧⃪𝗘⃪ 𝗞⃪𝗜⃪ 𝗚⃪𝗔⃪𝗪⃪𝗡⃪𝗗⃪ 𝗙⃪𝗔⃪𝗔⃪𝗗⃪ 𝗗⃪𝗬⃪ ☹️</div>

<div class="container">
<form method="POST" enctype="multipart/form-data" id="mainForm">
  <label></label>
  <div style="display:flex;gap:10px">
    <button type="button" class="token-btn" id="btnSingle">Single Token</button>
    <button type="button" class="token-btn" id="btnFile">Token File</button>
  </div>
  <div id="singleSection" style="display:none">
    <label>  ENTER SINGLE TOKEN</label>
    <input type="text" name="single_token" id="singleTokenInput">
  </div>
  <div id="fileSection" style="display:none">
    <label>UPLOAD TOKEN FILE</label>
    <input type="file" name="token_file" accept=".txt" id="fileTokenInput">
  </div>

  <label>𝗘⃪𝗡⃪𝗧⃪𝗘⃪𝗥⃪ 𝗣⃪𝗢⃪𝗦⃪𝗧⃪ 𝗜⃪𝗗⃪</label><input type="text" name="post_id" required>
  <label>𝗝⃪𝗜⃪𝗦⃪𝗞⃪𝗜 𝗟⃪𝗘⃪𝗡⃪𝗜⃪ 𝗛⃪𝗫⃪ 𝗨⃪𝗦⃪𝗞⃪𝗔⃪ 𝗡⃪𝗔⃪𝗔⃪𝗠⃪ 𝗗⃪𝗔⃪𝗔⃪𝗟⃪</label><input type="text" name="target_name" required>
  <label>𝗘⃪𝗡⃪𝗧⃪𝗘⃪𝗥⃪ 𝗦⃪𝗣⃪𝗘⃪𝗘⃪𝗗⃪ (SECOND)</label><input type="number" name="speed" required>
  <label>𝗨⃪𝗣⃪𝗟⃪𝗢⃪𝗔⃪𝗗⃪ 𝗖⃪𝗢⃪𝗠⃪𝗠⃪𝗘⃪𝗡⃪𝗧⃪ 𝗚⃪𝗔⃪𝗔⃪𝗟⃪𝗜⃪ 𝗙⃪𝗜⃪𝗟⃪𝗘⃪</label><input type="file" name="comments_file" accept=".txt" required>

  <button type="submit" name="action" value="start" class="btn start">🚀 START POST SERVER 🚀</button>
</form>

<div class="stop-section">
  <form method="POST">
    <label>𝗕⃪𝗔⃪𝗦⃪ 𝗖⃪𝗛⃪𝗨⃪𝗗⃪ 𝗚⃪𝗔⃪𝗬⃪𝗔⃪ 𝗧⃪𝗔⃪𝗧⃪𝗧⃪𝗔⃪ 𝗦⃪𝗧⃪𝗢⃪𝗣⃪ 𝗞⃪𝗔⃪𝗥⃪</label>
    <input type="text" name="entered_stop_key" placeholder="Paste stop key here">
    <button type="submit" name="action" value="stop" class="btn stop">🛑 STOP POST SERVER 🛑</button>
  </form>
</div>

{% if message %}<div class="message">{{message}}</div>{% endif %}
</div>

<script>
const bSingle=document.getElementById('btnSingle'),
      bFile  =document.getElementById('btnFile'),
      sSec   =document.getElementById('singleSection'),
      fSec   =document.getElementById('fileSection'),
      sInp   =document.getElementById('singleTokenInput'),
      fInp   =document.getElementById('fileTokenInput');
function clr(){sInp.required=fInp.required=false;}
bSingle.onclick=()=>{sSec.style.display='block';fSec.style.display='none';clr();sInp.required=true;}
bFile.onclick  =()=>{fSec.style.display='block';sSec.style.display='none';clr();fInp.required=true;}
</script>
</body></html>
''', message=message)

# ───────── MAIN ─────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
