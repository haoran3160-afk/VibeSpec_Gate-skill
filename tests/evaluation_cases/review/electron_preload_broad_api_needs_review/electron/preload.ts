import { contextBridge } from "electron";
import fs from "fs";

contextBridge.exposeInMainWorld("files", {
  writeFile(path: string, contents: string) {
    fs.writeFileSync(path, contents);
  },
});
