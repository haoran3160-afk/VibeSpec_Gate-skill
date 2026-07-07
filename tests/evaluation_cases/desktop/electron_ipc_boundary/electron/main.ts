import { ipcMain } from "electron";
ipcMain.handle("open-file", async () => "ok");
