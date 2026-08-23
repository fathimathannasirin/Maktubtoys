"# Maktub-Trading" 

## Deployment Notes

Before hosting, set these environment variables:

- `DEBUG=False`
- `SECRET_KEY=<long random secret key>`
- `ALLOWED_HOSTS=<comma-separated hostnames>`
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_SECONDS=31536000`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- `SECURE_HSTS_PRELOAD=True`

Example `ALLOWED_HOSTS`:

`example.com,www.example.com`