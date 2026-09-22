# Broke-Proof security notes

Broke-Proof handles personal transaction data, so the v1 implementation uses a conservative data model and avoids bank-account linking entirely.

## Implemented in this repository

- Passwords are salted and hashed using PBKDF2-SHA256 with 210,000 iterations; plaintext passwords are never stored.
- Access and refresh JWTs are signed server-side. Production deployments must replace the development secret with a long random value.
- API money inputs are validated by Pydantic and stored in fixed-precision decimal columns.
- OCR/LLM-parsed transactions are returned as a preview first; they are not persisted until the user confirms them.
- File upload type and size are checked before OCR.
- CORS origins are allow-listed through configuration.
- Raw pasted/OCR text is stored only when the user confirms the extracted transaction. If minimizing retained data is preferred, remove `source_text` persistence entirely.

## Production controls required

- Use a managed MySQL service with encrypted storage/volume encryption and encrypted backups.
- Terminate TLS at the hosting layer and allow only HTTPS externally.
- Store `SECRET_KEY`, database credentials, and optional LLM credentials in a secrets manager, not `.env` committed to source control.
- Enable database least-privilege accounts, audit logs, backup retention, and restore testing.
- Define retention/deletion rules for transaction and PII data in line with the DPDP Act and the organization's privacy policy.
- If an external OCR or LLM provider is enabled, disclose that processor, minimize payloads, and do not send full account identifiers when they are unnecessary.
- Add rate limiting, login lockout/abuse controls, email verification, and production observability before public launch.
