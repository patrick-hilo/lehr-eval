# Lehr-Evaluation

Minimal on-premises web app for anonymous classroom evaluations.

## Local Validation

- Run the end-to-end smoke scope with `uv run pytest tests/test_e2e_scope.py -v`.
- Run the full suite with `uv run pytest -v`.
- For manual local checks, start the app with `LEHR_EVAL_ADMIN_PASSWORD=secret uv run uvicorn --app-dir src lehr_eval.app:create_app --factory --reload --host 127.0.0.1 --port 8000` and open `http://127.0.0.1:8000/admin/login` or `http://127.0.0.1:8000/health`.

## Production Notes

- Publish QR URLs with a stable HTTPS DNS name such as `https://eval.schule.example`, not an IP address.
- Terminate HTTPS at Caddy and proxy the app to `127.0.0.1:8000`.
- Run the app as an unprivileged `lehr-eval` system user.
- Store the SQLite database at `/var/lib/lehr-eval/eval.db`.
- The systemd unit uses `StateDirectory=lehr-eval` so `/var/lib/lehr-eval` is created for that user.
- Set `LEHR_EVAL_ADMIN_PASSWORD` to a strong school-internal admin password before starting the service.
- Run `ops/backup-sqlite.sh` daily from cron or a systemd timer and write the consistent SQLite backup to separate school storage.
- Test restores regularly and record the result.
