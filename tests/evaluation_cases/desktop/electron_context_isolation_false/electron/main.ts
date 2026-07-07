import { BrowserWindow } from "electron";

new BrowserWindow({
  webPreferences: {
    nodeIntegration: false,
    contextIsolation: false
  }
});
