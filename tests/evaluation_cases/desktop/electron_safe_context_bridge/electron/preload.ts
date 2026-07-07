import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("appInfo", {
  version: () => "1.0.0"
});
