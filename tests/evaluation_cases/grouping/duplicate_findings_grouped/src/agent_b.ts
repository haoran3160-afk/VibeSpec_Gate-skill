import OpenAI from "openai";
import { exec } from "child_process";
export const system_prompt = "system prompt";
export function b(){ new OpenAI(); exec("node b.js"); }
