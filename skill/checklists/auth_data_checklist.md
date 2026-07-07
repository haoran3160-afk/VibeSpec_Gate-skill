# Auth and Data Checklist

- Do not trust frontend-only authorization.
- Verify mutating API routes check session/user/token.
- Verify id-based reads, updates, and deletes include owner or tenant checks.
- For Supabase, check RLS and policies for user-owned tables.
- For Firebase, reject broad `allow read, write: if true` rules.
- Mark complex policy correctness as manual-review-required.
