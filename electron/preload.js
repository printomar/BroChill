const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('cg', {
  dismiss: () => ipcRenderer.send('dismiss'),
});
