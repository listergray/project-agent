# -*- coding: utf-8 -*-
from pathlib import Path

u = lambda *cs: "".join(chr(c) for c in cs)

# Chinese labels via codepoints to keep this file ASCII-safe on Windows toolchains
T_TITLE = u(0x6296, 0x97F3) + u(0x76EE, 0x5F55) + u(0x53D1, 0x89C6, 0x9891)
T_SUB = (
    u(0x65B9, 0x6848) + " B" + u(0xFF1A)
    + "Playwright "
    + u(0x767B, 0x5F55, 0x521B, 0x4F5C, 0x8005, 0x4E2D, 0x5FC3, 0xFF0C)
    + u(0x626B, 0x63CF, 0x76EE, 0x5F55) + " mp4 "
    + u(0x5E76, 0x4E00, 0x952E, 0x53D1, 0x5E03, 0x3002)
    + u(0x9875, 0x9762, 0x7ED3, 0x6784, 0x53D8, 0x66F4, 0x65F6, 0x53EF, 0x80FD, 0x9700, 0x8981, 0x8C03, 0x6574, 0x9009, 0x62E9, 0x5668, 0x3002)
)
L_DIR = u(0x89C6, 0x9891, 0x76EE, 0x5F55)
B_SAVE_SCAN = u(0x4FDD, 0x5B58, 0x5E76, 0x626B, 0x63CF)
B_SCAN = u(0x4EC5, 0x626B, 0x63CF)
L_LOGIN = u(0x767B, 0x5F55, 0x72B6, 0x6001)
B_QR = u(0x626B, 0x7801, 0x767B, 0x5F55)
B_REFRESH = u(0x5237, 0x65B0, 0x72B6, 0x6001)
B_KEEPALIVE = u(0x7ACB, 0x5373, 0x4FDD, 0x6D3B)
L_HEADLESS = u(0x65E0, 0x5934, 0x6A21, 0x5F0F) + u(0xFF08, 0x4E0D, 0x63A8, 0x8350, 0xFF09)
HINT = (
    u(0x9996, 0x6B21, 0x8BF7, 0x70B9)
    + u(0x300C) + B_QR + u(0x300D)
    + u(0xFF0C, 0x5728, 0x5F39, 0x51FA, 0x6D4F, 0x89C8, 0x5668, 0x4E2D, 0x767B, 0x5F55)
    + u(0x6296, 0x97F3, 0x521B, 0x4F5C, 0x8005, 0x4E2D, 0x5FC3)
    + u(0xFF1B, 0x767B, 0x5F55, 0x6001, 0x4FDD, 0x5B58, 0x5728, 0x672C, 0x5730) + " profile"
    + u(0xFF1B)
    + u(0x670D, 0x52A1, 0x4F1A, 0x5B9A, 0x671F, 0x8BBF, 0x95EE, 0x521B, 0x4F5C, 0x8005, 0x4E2D, 0x5FC3, 0x4FDD, 0x6D3B, 0xFF08)
    + "45min"
    + u(0xFF09, 0x3002)
)
L_LIST = u(0x89C6, 0x9891, 0x5217, 0x8868)
B_JOBS = u(0x5237, 0x65B0, 0x4EFB, 0x52A1)
H_FILE = u(0x6587, 0x4EF6)
H_TITLE = u(0x6807, 0x9898)
H_COVER = u(0x5C01, 0x9762)
H_SIZE = u(0x5927, 0x5C0F)
H_OP = u(0x64CD, 0x4F5C)
B_PUB = u(0x53D1, 0x5E03, 0x5230, 0x6296, 0x97F3)
L_JOBS = u(0x6700, 0x8FD1, 0x4EFB, 0x52A1)
H_STATUS = u(0x72B6, 0x6001)
H_MSG = u(0x6D88, 0x606F)
H_TIME = u(0x65F6, 0x95F4)
NONE = u(0x65E0)
UNKNOWN = u(0x672A, 0x77E5)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{T_TITLE}</title>
  <style>
    :root {{
      --bg: #0f1419; --panel: #1a2332; --line: #2a3648; --text: #e7eef8;
      --muted: #8b9bb4; --accent: #fe2c55; --ok: #3dd68c; --warn: #f5a524; --bad: #f31260;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: radial-gradient(1200px 600px at 10% -10%, #2a1830 0%, transparent 50%),
                  radial-gradient(900px 500px at 100% 0%, #12263d 0%, transparent 45%), var(--bg);
      color: var(--text); min-height: 100vh;
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 28px 20px 60px; }}
    h1 {{ margin: 0 0 6px; font-size: 28px; }}
    .sub {{ color: var(--muted); margin-bottom: 24px; }}
    .card {{
      background: #1a2332ee; border: 1px solid var(--line);
      border-radius: 14px; padding: 18px; margin-bottom: 16px;
    }}
    .row {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
    label {{ color: var(--muted); font-size: 13px; min-width: 72px; }}
    input[type="text"] {{
      flex: 1; min-width: 260px; background: #0d121a; border: 1px solid var(--line);
      color: var(--text); border-radius: 10px; padding: 10px 12px; outline: none;
    }}
    button {{
      border: 0; border-radius: 10px; padding: 10px 14px; cursor: pointer;
      font-weight: 600; color: white; background: #334155;
    }}
    button.primary {{ background: linear-gradient(135deg, #fe2c55, #ff6a3d); }}
    button.ok {{ background: #178f5b; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 10px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); }}
    .tag {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; background: #243044; color: var(--muted); }}
    .tag.ok {{ background: #123526; color: var(--ok); }}
    .tag.bad {{ background: #3a1320; color: var(--bad); }}
    .tag.run {{ background: #3a2a10; color: var(--warn); }}
    .muted {{ color: var(--muted); font-size: 12px; }}
    .path {{ word-break: break-all; }}
    .toast {{
      position: fixed; right: 18px; bottom: 18px; background: #111827; border: 1px solid var(--line);
      padding: 12px 14px; border-radius: 12px; max-width: 420px; display: none;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{T_TITLE}</h1>
    <p class="sub">{T_SUB}</p>
    <div class="card">
      <div class="row" style="margin-bottom:12px">
        <label>{L_DIR}</label>
        <input id="videoDir" type="text" placeholder=".../EP29_wechat_voice/video_html" />
        <button class="primary" onclick="saveAndScan()">{B_SAVE_SCAN}</button>
        <button onclick="scanOnly()">{B_SCAN}</button>
      </div>
      <div class="row">
        <label>{L_LOGIN}</label>
        <span id="loginTag" class="tag">{UNKNOWN}</span>
        <button class="ok" onclick="doLogin()">{B_QR}</button>
        <button onclick="refreshLogin(true)">{B_REFRESH}</button>
        <button onclick="doKeepAlive()">{B_KEEPALIVE}</button>
        <label style="margin-left:12px"><input id="headless" type="checkbox" /> {L_HEADLESS}</label>
      </div>
      <p class="muted" style="margin:8px 0 0" id="keepAliveInfo"></p>
      <p class="muted" style="margin:8px 0 0">{HINT}</p>
    </div>
    <div class="card">
      <div class="row" style="justify-content:space-between;margin-bottom:10px">
        <div><strong>{L_LIST}</strong> <span id="scanInfo" class="muted"></span></div>
        <button onclick="loadJobs()">{B_JOBS}</button>
      </div>
      <table>
        <thead>
          <tr>
            <th style="width:28%">{H_FILE}</th>
            <th style="width:18%">{H_TITLE}</th>
            <th style="width:18%">{H_COVER}</th>
            <th style="width:12%">{H_SIZE}</th>
            <th style="width:24%">{H_OP}</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div class="card">
      <strong>{L_JOBS}</strong>
      <table style="margin-top:10px">
        <thead>
          <tr><th>ID</th><th>{H_TITLE}</th><th>{H_STATUS}</th><th>{H_MSG}</th><th>{H_TIME}</th></tr>
        </thead>
        <tbody id="jobs"></tbody>
      </table>
    </div>
  </div>
  <div id="toast" class="toast"></div>
  <script>
    const NONE_LABEL = {NONE!r};
    const PUB_LABEL = {B_PUB!r};
    const $ = (id) => document.getElementById(id);
    function toast(msg) {{
      const el = $('toast'); el.textContent = msg; el.style.display = 'block';
      setTimeout(() => el.style.display = 'none', 3200);
    }}
    function fmtSize(n) {{
      if (n < 1024) return n + ' B';
      if (n < 1024*1024) return (n/1024).toFixed(1) + ' KB';
      return (n/1024/1024).toFixed(1) + ' MB';
    }}
    async function api(url, opts = {{}}) {{
      const res = await fetch(url, {{ headers: {{ 'Content-Type': 'application/json' }}, ...opts }});
      const data = await res.json().catch(() => ({{}}));
      if (!res.ok) throw new Error(data.detail || data.message || res.statusText);
      return data;
    }}
    function escapeHtml(s) {{
      return String(s).replace(/[&<>"']/g, (c) => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
    }}
    function sleep(ms) {{ return new Promise(r => setTimeout(r, ms)); }}
    async function loadSettings() {{
      const s = await api('/api/settings');
      $('videoDir').value = s.videoDir || '';
      $('headless').checked = !!s.headless;
    }}
    async function saveSettings() {{
      await api('/api/settings', {{
        method: 'PUT',
        body: JSON.stringify({{ videoDir: $('videoDir').value.trim(), headless: $('headless').checked }}),
      }});
    }}
    async function saveAndScan() {{ await saveSettings(); await scanOnly(); toast('OK'); }}
    async function scanOnly() {{
      const directory = $('videoDir').value.trim();
      const data = await api('/api/scan', {{ method: 'POST', body: JSON.stringify({{ directory }}) }});
      $('scanInfo').textContent = data.directory + ' | ' + data.total;
      const tb = $('tbody'); tb.innerHTML = '';
      for (const it of data.list) {{
        const tr = document.createElement('tr');
        const coverName = it.coverPath ? it.coverPath.split(/[/\\\\]/).pop() : NONE_LABEL;
        tr.innerHTML = `
          <td><div>${{escapeHtml(it.name)}}</div><div class="muted path">${{escapeHtml(it.path)}}</div></td>
          <td><input class="title-input" type="text" style="min-width:140px;width:100%" /></td>
          <td class="muted">${{escapeHtml(coverName)}}</td>
          <td>${{fmtSize(it.size)}}</td>
          <td><button class="primary pub-btn">${{PUB_LABEL}}</button></td>`;
        tr.querySelector('.title-input').value = it.title || '';
        tr.querySelector('.pub-btn').addEventListener('click', () => {{
          publishOne(it.path, it.coverPath || '', tr.querySelector('.title-input').value.trim());
        }});
        tb.appendChild(tr);
      }}
    }}
    async function publishOne(videoPath, coverPath, title) {{
      try {{
        const data = await api('/api/publish', {{
          method: 'POST',
          body: JSON.stringify({{ videoPath, title: title || undefined, coverPath: coverPath || null }}),
        }});
        toast('job ' + data.jobId);
        loadJobs(); pollJob(data.jobId);
      }} catch (e) {{ toast(String(e.message || e)); }}
    }}
    async function pollJob(id) {{
      for (let i = 0; i < 120; i++) {{
        await sleep(2000);
        try {{
          const j = await api('/api/jobs/' + id);
          loadJobs();
          if (j.status === 'SUCCESS' || j.status === 'FAILED') {{ toast(j.status + ': ' + (j.message || '')); return; }}
        }} catch (_) {{}}
      }}
    }}
    async function loadJobs() {{
      const data = await api('/api/jobs');
      const tb = $('jobs'); tb.innerHTML = '';
      for (const j of data.list) {{
        const cls = j.status === 'SUCCESS' ? 'ok' : j.status === 'FAILED' ? 'bad' : 'run';
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${{j.id}}</td><td>${{escapeHtml(j.title || '')}}</td>
          <td><span class="tag ${{cls}}">${{j.status}}</span></td>
          <td class="muted">${{escapeHtml(j.message || '')}}</td>
          <td class="muted">${{j.updatedAt ? new Date(j.updatedAt).toLocaleString() : '-'}}</td>`;
        tb.appendChild(tr);
      }}
    }}
    function renderKeepAlive(ka) {{
      const el = $('keepAliveInfo');
      if (!el || !ka) return;
      const last = ka.lastAt ? new Date(ka.lastAt).toLocaleString() : '-';
      const next = ka.nextAt ? new Date(ka.nextAt).toLocaleString() : '-';
      const st = ka.lastOk === true ? '\u6709\u6548' : (ka.lastOk === false ? '\u5931\u6548/\u672a\u767b\u5f55' : '\u5c1a\u672a\u68c0\u6d4b');
      const jitter = ka.jitterMin != null ? `\u00b1${{ka.jitterMin}}` : '';
      const delay = ka.lastDelayMin != null ? ` | \u672c\u6b21\u95f4\u9694: ${{ka.lastDelayMin}}min` : '';
      el.textContent = `\u4fdd\u6d3b: ${{ka.enabled ? '\u5f00' : '\u5173'}} / ${{ka.intervalMin || '-'}}${{jitter}}min${{delay}} | \u4e0a\u6b21: ${{last}} (${{st}}) | \u4e0b\u6b21: ${{next}} | ${{ka.lastMessage || ''}}`;
    }}
    async function doKeepAlive() {{
      toast('\u6b63\u5728\u4fdd\u6d3b...');
      try {{
        const r = await api('/api/login/keepalive', {{ method: 'POST' }});
        renderKeepAlive(r);
        toast(r.lastMessage || (r.lastOk ? 'OK' : 'NO'));
        const tag = $('loginTag');
        tag.textContent = r.lastMessage || (r.lastOk ? 'OK' : 'NO');
        tag.className = 'tag ' + (r.lastOk ? 'ok' : 'bad');
      }} catch (e) {{ toast(String(e.message || e)); }}
    }}
    async function doLogin() {{
      toast('\u7b49\u5f85\u6d4f\u89c8\u5668\u7a7a\u95f2\u5e76\u6253\u5f00\u626b\u7801...');
      try {{
        const r = await api('/api/login', {{ method: 'POST' }});
        toast(r.message || '');
        if (r.keepAlive) renderKeepAlive(r.keepAlive);
        if (r.ok) {{
          const tag = $('loginTag');
          tag.textContent = r.message || 'OK';
          tag.className = 'tag ok';
        }} else {{
          refreshLogin();
        }}
      }} catch (e) {{ toast(String(e.message || e)); }}
    }}
    let loginBusy = false;
    async function refreshLogin(force) {{
      if (loginBusy) return;
      loginBusy = true;
      const tag = $('loginTag');
      tag.textContent = '...';
      tag.className = 'tag run';
      try {{
        const q = force ? '?force=1' : '?soft=1';
        const r = await api('/api/login/status' + q);
        const suffix = r.fromDisk ? '(\u7f13\u5b58)' : (r.cached ? '(\u5185\u5b58)' : '');
        tag.textContent = (r.message || (r.ok ? 'OK' : 'NO')) + suffix;
        tag.className = 'tag ' + (r.ok ? 'ok' : 'bad');
        if (r.keepAlive) renderKeepAlive(r.keepAlive);
      }} catch (e) {{
        tag.textContent = String(e.message || e).slice(0, 24) || 'ERR';
        tag.className = 'tag bad';
      }} finally {{
        loginBusy = false;
      }}
    }}
    (async () => {{
      await loadSettings(); await loadJobs();
      if ($('videoDir').value.trim()) {{ try {{ await scanOnly(); }} catch (e) {{ toast(e.message); }} }}
      try {{
        const s = await api('/api/settings');
        if (s.keepAlive) renderKeepAlive(s.keepAlive);
      }} catch (_) {{}}
      // After restart: soft status from disk cache (browser profile also persists).
      try {{ await refreshLogin(false); }} catch (_) {{
        $('loginTag').textContent = '\u70b9\u5237\u65b0\u68c0\u6d4b';
        $('loginTag').className = 'tag';
      }}
    }})();
  </script>
</body>
</html>
"""

out = Path(__file__).resolve().parents[1] / "web" / "index.html"
out.write_text(html, encoding="utf-8")
print("wrote", out, T_TITLE in out.read_text(encoding="utf-8"))
