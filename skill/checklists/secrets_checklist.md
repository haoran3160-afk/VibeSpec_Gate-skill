# Secrets Checklist

- Look for `.env`, `.env.local`, `.env.production`, logs, README, fixtures, and test data containing real values.
- Check OpenAI, Anthropic, Stripe, Supabase, Firebase, GitHub tokens, private keys, and database URLs.
- Treat service role keys and private keys as P0 when exposed.
- Mask all secret evidence.
- Recommend key rotation and git history scanning for confirmed leaks.
