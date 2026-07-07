import OpenAI from "openai";
import { exec } from "child_process";
export const system_prompt = "system prompt";
export function c(){ new OpenAI(); exec("node c.js"); }
