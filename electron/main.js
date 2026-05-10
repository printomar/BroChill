const { app, BrowserWindow, ipcMain } = require('electron');
const http = require('http');
const path = require('path');
const fs = require('fs');

const config = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'config.json'), 'utf8'));
const PORT = config.overlay?.port ?? 8765;

let win;

function createWindow() {
  win = new BrowserWindow({
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    fullscreen: true,
    skipTaskbar: true,
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  win.setIgnoreMouseEvents(true);
}

function startServer() {
  const server = http.createServer((req, res) => {
    if (req.method !== 'POST' || req.url !== '/trigger') {
      res.writeHead(404).end();
      return;
    }

    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { bit_id } = JSON.parse(body);
        const htmlPath = path.join(__dirname, 'renderer', `${bit_id}.html`);
        if (!fs.existsSync(htmlPath)) {
          res.writeHead(404).end('bit not found');
          return;
        }
        win.loadFile(htmlPath);
        win.setIgnoreMouseEvents(false);
        win.show();
        res.writeHead(200).end('ok');
      } catch {
        res.writeHead(400).end('bad request');
      }
    });
  });

  server.listen(PORT, '127.0.0.1', () => {
    console.log(`overlay server on port ${PORT}`);
  });
}

ipcMain.on('dismiss', () => {
  win.hide();
  win.setIgnoreMouseEvents(true);
});

app.whenReady().then(() => {
  createWindow();
  startServer();
});

// Stay alive even when the window is hidden
app.on('window-all-closed', e => e.preventDefault());
