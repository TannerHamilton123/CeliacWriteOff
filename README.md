# CeliacWriteOff
Upload receipts and categorize expenses related to Celiac's for tax US write-offs

## Environment variables

Backend: copy `.env.example` to `.env` in the repo root and fill in what you
need. See the comments in that file for what each variable does and which
ones have a local-dev-only bypass when left unset (`RECAPTCHA_SECRET_KEY`,
`SENDGRID_API_KEY`/`RESET_EMAIL_FROM`) -- never leave those unset in
production.

Frontend: copy `src/celiacwriteoff/frontend/.env.example` to
`src/celiacwriteoff/frontend/.env` and fill in `VITE_RECAPTCHA_SITE_KEY` to
match the backend's `RECAPTCHA_SECRET_KEY`.

## Admin access

There's no self-service way to become an admin. To promote an existing
account so it can view the login-activity log, run:

```sh
sqlite3 data/celiacwriteoff.db "UPDATE users SET is_admin = 1 WHERE email = 'someone@example.com';"
```
