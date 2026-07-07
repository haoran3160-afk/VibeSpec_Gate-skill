import { BrowserWindow } from "electron";

new BrowserWindow({
  webPreferences: {
    nodeIntegration: true,
    contextIsolation: true
  }
});
