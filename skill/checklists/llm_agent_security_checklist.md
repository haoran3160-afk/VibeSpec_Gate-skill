# LLM and Agent Security Checklist

- Check for system prompt exposure.
- Check whether user input can alter tool policy or system instructions.
- Check high-risk tools: shell, file write/delete, database write, email, payment, external APIs.
- Require least privilege, allowlists, audit logs, rate limits, token/budget limits, and human confirmation for high-risk operations.
- Check for logging of full prompts, conversations, secrets, or private data.
- Mark unknown tool governance as review-required.
