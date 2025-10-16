const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = process.env.NODE_ENV !== 'production';
let pythonProc = null;

function launchPython() {
  const projectRoot = path.resolve(__dirname, '..', '..');
  const venvPython = path.join(projectRoot, 'venv', 'Scripts', 'python.exe');
  const script = path.join(projectRoot, 'src', 'gui', 'main_window.py');

  const env = { ...process.env, PYTHONPATH: projectRoot };
  pythonProc = spawn(venvPython, [script], { cwd: projectRoot, env, stdio: 'inherit' });
  pythonProc.on('close', (code) => {
    pythonProc = null;
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 960,
    height: 640,
    title: 'NeoMeme Markets Launcher',
    webPreferences: { nodeIntegration: true }
  });

  const html = `<!doctype html><html><head><meta charset="utf-8"/><title>NeoMeme Markets</title>
  <style>body{font-family:Inter,Segoe UI,Arial;background:#0b1220;color:#eaeef7;margin:0;display:flex;align-items:center;justify-content:center;height:100vh} .card{background:#121a2b;border:1px solid #1f2740;border-radius:12px;padding:24px;max-width:720px;box-shadow:0 10px 30px rgba(0,0,0,.35)} h1{margin:0 0 8px} p{opacity:.8} .btn{margin-top:16px;background:linear-gradient(90deg,#00f5d4,#00b3f0);color:#001018;border:none;border-radius:8px;padding:12px 16px;font-weight:700;cursor:pointer} .sub{font-size:12px;opacity:.65;margin-top:8px}</style>
  </head><body><div class="card"><h1>NeoMeme Markets</h1><p>Python GUI will launch in a separate window.</p><button class="btn" onclick="openLogs()">Open Logs Folder</button><div class="sub">Close this window to quit the launcher.</div></div>
  <script>function openLogs(){require('electron').shell.openPath('logs')}</script></body></html>`;
  win.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(html));
}

app.whenReady().then(() => {
  launchPython();
  createWindow();
});

app.on('before-quit', () => {
  if (pythonProc) {
    try { pythonProc.kill(); } catch (e) {}
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});


