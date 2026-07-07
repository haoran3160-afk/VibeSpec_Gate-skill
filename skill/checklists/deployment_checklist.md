# Deployment Checklist

- Check CORS wildcard usage on authenticated APIs.
- Check session cookies for httpOnly, secure, and sameSite.
- Check debug and verbose logging in production config.
- Check production source-map exposure.
- Check baseline security headers or hosting-layer equivalent.
- Do not run dynamic scans without explicit authorization.
