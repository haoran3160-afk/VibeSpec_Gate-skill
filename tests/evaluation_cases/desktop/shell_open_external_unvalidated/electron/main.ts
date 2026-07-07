import { shell } from "electron";

export function openLink(url: string) {
  return shell.openExternal(url);
}
