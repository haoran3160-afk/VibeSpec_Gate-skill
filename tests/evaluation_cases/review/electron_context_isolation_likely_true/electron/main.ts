import { BrowserWindow } from "electron";

export function createWindow() {
  return new BrowserWindow({
    webPreferences: {
      contextIsolation: false,
      nodeIntegration: false,
    },
  });
}
