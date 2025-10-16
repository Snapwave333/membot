const { app, BrowserWindow, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, spawnSync } = require('child_process');
const { pathToFileURL } = require('url');
const isDev = process.env.NODE_ENV !== 'production';
let pythonProc = null;

function exists(p) {
  try { return fs.existsSync(p); } catch { return false; }
}

function which(cmd) {
  const res = spawnSync(process.platform === 'win32' ? 'where' : 'which', [cmd], { encoding: 'utf8' });
  if (res.status === 0 && res.stdout) {
    const line = res.stdout.split(/\r?\n/).filter(Boolean)[0];
    return line;
  }
  return null;
}

function detectPyVersions() {
  // Returns map like { '3.13t': 'C:\\Program Files\\Python313\\python3.13t.exe', '3.13': '...python.exe', '3.11': '...python.exe' }
  const versions = {};
  if (process.platform !== 'win32') return versions;
  const r = spawnSync('py', ['-0p'], { encoding: 'utf8' });
  if (r.status !== 0 || !r.stdout) return versions;
  const lines = r.stdout.split(/\r?\n/).filter(Boolean);
  lines.forEach(line => {
    const m = line.match(/-V:(\S+)\s+(.*python[^\s]*\.exe)/i);
    if (m) versions[m[1]] = m[2];
  });
  return versions;
}

function choosePythonLauncherArg() {
  // Prefer 3.12 or 3.11 over 3.13t to avoid CFFI incompatibility
  if (process.platform !== 'win32') return null;
  const versions = detectPyVersions();
  const hasPrefix = (prefix) => Object.keys(versions).some(v => v.startsWith(prefix));
  if (hasPrefix('3.12')) return '-3.12';
  if (hasPrefix('3.11')) return '-3.11';
  // Fall back to default 3.x
  return '-3';
}

function run(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { stdio: 'inherit', ...opts });
    p.on('error', reject);
    p.on('close', (code) => code === 0 ? resolve() : reject(new Error(`${cmd} exited with code ${code}`)));
  });
}

async function bootstrapVenv(resourcesPath) {
  const venvDir = path.join(resourcesPath, 'venv');
  const venvPython = path.join(venvDir, 'Scripts', 'python.exe');
  if (exists(venvPython)) return venvPython;

  // Try to find a system Python (py launcher preferred on Windows)
  let pyLauncher = which('py');
  let sysPython = which('python');
  const createArgs = ['-m', 'venv', venvDir];
  try {
    if (process.platform === 'win32' && pyLauncher) {
      const arg = choosePythonLauncherArg();
      await run(pyLauncher, [arg, ...createArgs]);
    } else if (sysPython) {
      await run(sysPython, createArgs);
    } else {
      throw new Error('Python not found in PATH. Please install Python 3.x');
    }
  } catch (e) {
    dialog.showErrorBox('Python Setup Failed', `${e.message}`);
    throw e;
  }

  // Install requirements into the newly created venv
  const reqPath = path.join(resourcesPath, 'requirements.txt');
  if (exists(reqPath)) {
    try {
      await run(venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel']);
      await run(venvPython, ['-m', 'pip', 'install', '-r', reqPath]);
    } catch (e) {
      dialog.showErrorBox('Dependency Installation Failed', `Failed to install requirements from ${reqPath}. Error: ${e.message}`);
      throw e;
    }
  } else {
    dialog.showMessageBox({ type: 'warning', title: 'Requirements Missing', message: 'requirements.txt was not found in resources. The GUI may fail if dependencies are missing.' });
  }

  return venvPython;
}

async function launchPython() {
  const resourcesPath = isDev ? path.resolve(__dirname, '..', '..') : process.resourcesPath;
  const script = isDev
    ? path.join(resourcesPath, 'src', 'gui', 'main_window.py')
    : path.join(resourcesPath, 'src', 'gui', 'main_window.py'); // shipped via extraResource

  let pythonExe = isDev
    ? path.join(resourcesPath, 'venv', 'Scripts', 'python.exe')
    : path.join(resourcesPath, 'venv', 'Scripts', 'python.exe');

  // If packaged and venv is missing, bootstrap it
  if (!exists(pythonExe)) {
    try {
      pythonExe = await bootstrapVenv(resourcesPath);
    } catch (e) {
      // fallback to system python if available
      const sysPy = which('python') || which('py');
      if (!sysPy) throw e;
      pythonExe = sysPy;
    }
  }

  const env = { ...process.env, PYTHONPATH: resourcesPath, PYTHONUTF8: '1' };
  try {
    pythonProc = spawn(pythonExe, [script], { cwd: resourcesPath, env, stdio: 'inherit' });
    pythonProc.on('close', () => { pythonProc = null; });
    pythonProc.on('error', (err) => {
      dialog.showErrorBox('Launch Error', `Failed to start Python GUI. ${err.message}`);
    });
  } catch (err) {
    dialog.showErrorBox('Launch Error', `Failed to spawn Python at ${pythonExe}. ${err.message}`);
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 960,
    height: 640,
    title: 'NeoMeme Markets Launcher',
    webPreferences: { nodeIntegration: true }
  });

  const resourcesPath = isDev ? path.resolve(__dirname, '..', '..') : process.resourcesPath;
  const logDir = path.join(resourcesPath, 'logs');
  try { if (!exists(logDir)) fs.mkdirSync(logDir, { recursive: true }); } catch {}

  // Use original logo for splash (remove custom banner)
  const logoPath = path.join(resourcesPath, 'assets', 'sprites', 'logo_main.png');
  const bannerUrl = pathToFileURL(logoPath).href;

  const html = `<!doctype html><html><head><meta charset="utf-8"/><title>NeoMeme Markets</title>
  <style>body{font-family:Inter,Segoe UI,Arial;background:#0b1220;color:#eaeef7;margin:0;display:flex;align-items:center;justify-content:center;height:100vh} .card{background:#121a2b;border:1px solid #1f2740;border-radius:12px;padding:24px;max-width:720px;box-shadow:0 10px 30px rgba(0,0,0,.35)} h1{margin:8px 0 8px} p{opacity:.8} .btn{margin-top:16px;background:linear-gradient(90deg,#00f5d4,#00b3f0);color:#001018;border:none;border-radius:8px;padding:12px 16px;font-weight:700;cursor:pointer} .sub{font-size:12px;opacity:.65;margin-top:8px} .logo{display:block;margin:0 auto 8px auto;max-width:100%;width:420px}</style>
  </head><body><div class="card"><img class="logo" src="${bannerUrl}" alt="NeoMeme Markets"/><h1>NeoMeme Markets</h1><p>Python GUI will launch in a separate window.</p><button class="btn" onclick="openLogs()">Open Logs Folder</button><div class="sub">Close this window to quit the launcher.</div></div>
  <script>function openLogs(){require('electron').shell.openPath('${logDir.replace(/\\/g, '\\\\')}')}</script></body></html>`;
  win.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(html));
}

app.whenReady().then(async () => {
  await launchPython();
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


