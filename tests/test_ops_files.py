from pathlib import Path


def test_ops_files_document_dns_https_and_backups():
    readme = Path("README.md").read_text()
    caddy = Path("ops/Caddyfile.example").read_text()
    backup = Path("ops/backup-sqlite.sh").read_text()

    assert "DNS" in readme
    assert "SQLite" in readme
    assert "reverse_proxy" in caddy
    assert "sqlite" in backup.lower()


def test_ops_files_cover_production_operating_contract():
    readme = Path("README.md").read_text()
    caddy = Path("ops/Caddyfile.example").read_text()
    service = Path("ops/lehr-eval.service").read_text()
    backup = Path("ops/backup-sqlite.sh").read_text()

    assert "DNS name" in readme
    assert "not an IP address" in readme
    assert "https://" in readme.lower()
    assert "https://eval.schule.example" in caddy
    assert "restore" in readme.lower()
    assert "127.0.0.1:8000" in caddy
    assert "User=lehr-eval" in service
    assert "Group=lehr-eval" in service
    assert "StateDirectory=lehr-eval" in service
    assert "--app-dir /opt/lehr-eval/src" in service
    assert "LEHR_EVAL_ADMIN_PASSWORD" in readme
    assert "LEHR_EVAL_ADMIN_PASSWORD=change-this-before-start" in service
    assert "LEHR_EVAL_ADMIN_PASSWORD_HASH" not in readme
    assert "LEHR_EVAL_ADMIN_PASSWORD_HASH" not in service
    assert "/var/lib/lehr-eval/eval.db" in service
    assert "/var/lib/lehr-eval/eval.db" in backup
    assert ".backup" in backup
    assert "separate school storage" in backup
    assert "integrity_check" in backup
    assert ".tmp" in backup
    assert "mv" in backup
    assert '!= "ok"' in backup
    assert '[[ ! -f "$DB_PATH" ]]' in backup
