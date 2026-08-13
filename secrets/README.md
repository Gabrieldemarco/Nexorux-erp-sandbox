# Example secrets for docker-compose.prod.yml
# Copy this folder layout and fill real values. The real `secrets/` directory is gitignored.
#
# Required files (one secret per file, no trailing spaces ideally):
#   secrets/db_password.txt
#   secrets/redis_password.txt
#   secrets/secret_key.txt
#
# Optional SMTP:
#   secrets/smtp_password.txt
#   then set SMTP_PASSWORD_FILE=/run/secrets/smtp_password and add the secret in compose.
#
# Generate strong values, e.g.:
#   openssl rand -base64 32 > secrets/db_password.txt
#   openssl rand -base64 32 > secrets/redis_password.txt
#   openssl rand -base64 48 > secrets/secret_key.txt
#
# Never commit real secrets.

placeholder: see docs/PRODUCTION.md
