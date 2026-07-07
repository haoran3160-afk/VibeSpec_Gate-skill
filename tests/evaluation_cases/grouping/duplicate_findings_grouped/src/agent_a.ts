import OpenAI from "openai";
import { exec } from "child_process";
export const system_prompt = "system prompt";
export function a(){ new OpenAI(); exec("node a.js"); }
