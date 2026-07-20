const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("desktopApi", {
  readDocument: (documentId) => ipcRenderer.invoke("document:read", documentId),
});
