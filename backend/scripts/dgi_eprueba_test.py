#!/usr/bin/env python3
"""
DGI ePrueba readiness + sandbox test script.

Usage (from backend/):
    .venv311\\Scripts\\python.exe scripts/dgi_eprueba_test.py --dry-run
    .venv311\\Scripts\\python.exe scripts/dgi_eprueba_test.py --probe-network
    .venv311\\Scripts\\python.exe scripts/dgi_eprueba_test.py --send --fiscal-document-id <uuid>

Env:
    DGI_ENVIRONMENT=testing
    DGI_CERT_PATH=path/to/cert.pem
    DGI_KEY_PATH=path/to/key.pem
    DGI_KEY_PASSWORD=optional
    DATABASE_URL=...
"""

from __future__ import annotations

import argparse
import asyncio
import json
import socket
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.services.fiscal.dgi_client import DGI_ENDPOINTS


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _evidence_dir() -> Path:
    return ROOT.parent / "compliance" / "dgi" / "evidence"


def _test_cases_dir() -> Path:
    return ROOT.parent / "compliance" / "dgi" / "test-cases"


def _endpoint_url() -> str:
    if settings.DGI_WS_URL:
        return settings.DGI_WS_URL
    return DGI_ENDPOINTS.get(settings.DGI_ENVIRONMENT, {}).get("url", "unknown")


def _check_xsd(report: dict[str, Any]) -> None:
    xsd_dir = _evidence_dir() / "xsd"
    xsd_path = xsd_dir / "CFEDGI.xsd"
    if xsd_path.exists():
        version_file = xsd_dir / "version.txt"
        version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "unknown"
        report["checks"].append(
            {
                "name": "xsd_schema",
                "status": "ok",
                "entry_point": "CFEDGI.xsd",
                "xsd_package_version": version,
                "path": str(xsd_path),
            }
        )
    else:
        report["checks"].append(
            {
                "name": "xsd_schema",
                "status": "missing",
                "action": (
                    "Download XSDs_FE from "
                    "https://www.efactura.dgi.gub.uy/principal/ampliacion_de_contenido/documentos-de-interes"
                ),
            }
        )


def _check_pdf(report: dict[str, Any]) -> None:
    pdf_path = _evidence_dir() / "Formato_CFE_v25-2.pdf"
    if pdf_path.exists():
        report["checks"].append(
            {
                "name": "cfe_format_pdf",
                "status": "ok",
                "file": pdf_path.name,
                "size_bytes": pdf_path.stat().st_size,
            }
        )
    else:
        report["checks"].append(
            {
                "name": "cfe_format_pdf",
                "status": "missing",
                "note": "Formato CFE PDF is reference only; XSD is authoritative",
            }
        )


def _check_certificate(report: dict[str, Any]) -> None:
    cert_path = settings.DGI_CERT_PATH
    key_path = settings.DGI_KEY_PATH
    check: dict[str, Any] = {
        "name": "certificate",
        "cert_path": cert_path,
        "key_path": key_path,
    }

    if not cert_path or not key_path:
        check["status"] = "missing"
        check["action"] = (
            "Obtain ePrueba signing cert from your CA (Abitab/Correo/etc.), "
            "export PEM cert+key, set DGI_CERT_PATH and DGI_KEY_PATH in backend/.env"
        )
        report["checks"].append(check)
        return

    cert_file = Path(cert_path)
    key_file = Path(key_path)
    if not cert_file.exists() or not key_file.exists():
        check["status"] = "missing_files"
        check["cert_exists"] = cert_file.exists()
        check["key_exists"] = key_file.exists()
        report["checks"].append(check)
        return

    try:
        from app.services.fiscal.signer import load_certificate, load_private_key

        cert, _ = load_certificate(str(cert_file))
        password = settings.DGI_KEY_PASSWORD
        load_private_key(str(key_file), password=password)
        check["status"] = "ok"
        check["subject"] = cert.subject.rfc4514_string()
        # cryptography API: prefer UTC attribute when available
        not_after = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after
        if not_after.tzinfo is None:
            not_after = not_after.replace(tzinfo=timezone.utc)
        check["not_valid_after"] = not_after.isoformat()
        check["expired"] = not_after < datetime.now(timezone.utc)
        if check["expired"]:
            check["status"] = "expired"
    except Exception as exc:  # noqa: BLE001 — readiness report must never crash
        check["status"] = "invalid"
        check["error"] = str(exc)

    report["checks"].append(check)


def _probe_network(report: dict[str, Any], timeout: float = 10.0) -> None:
    url = _endpoint_url()
    check: dict[str, Any] = {"name": "endpoint_reachable", "url": url}

    if not url or url == "unknown":
        check["status"] = "misconfigured"
        report["checks"].append(check)
        return

    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        check["status"] = "misconfigured"
        report["checks"].append(check)
        return

    try:
        # DNS
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        check["dns_ok"] = True
        check["resolved"] = list({item[4][0] for item in infos})[:5]

        # TCP + TLS handshake (does not send SOAP)
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                check["tls_ok"] = True
                check["tls_version"] = ssock.version()
                check["cipher"] = ssock.cipher()[0] if ssock.cipher() else None
        check["status"] = "ok"
    except Exception as exc:  # noqa: BLE001
        check["status"] = "unreachable"
        check["error"] = str(exc)
        check["action"] = (
            "Open outbound HTTPS to efactura.dgi.gub.uy:6443 from this machine/network. "
            "Corporate firewall/VPN often blocks this port."
        )

    report["checks"].append(check)


def dry_run(*, probe_network: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "timestamp": _utc_now(),
        "mode": "dry-run",
        "environment": settings.DGI_ENVIRONMENT,
        "endpoint": _endpoint_url(),
        "cfe_xsd_validation_required": settings.CFE_XSD_VALIDATION_REQUIRED,
        "checks": [],
        "next_steps": [],
    }

    _check_xsd(report)
    _check_pdf(report)
    _check_certificate(report)
    if probe_network:
        _probe_network(report)
    else:
        report["checks"].append(
            {
                "name": "endpoint_reachable",
                "status": "skipped",
                "note": "Pass --probe-network to test TLS to DGI ePrueba",
            }
        )

    statuses = {c["name"]: c["status"] for c in report["checks"]}
    ready_local = statuses.get("xsd_schema") == "ok" and statuses.get("certificate") == "ok"
    ready_network = statuses.get("endpoint_reachable") == "ok"

    if ready_local and ready_network:
        report["readiness"] = "ready_for_live_send"
        report["next_steps"].append(
            "Issue a signed CFE in the UI (Fiscal Documents → Emitir), then run "
            "`--send --fiscal-document-id <uuid>`"
        )
    elif ready_local:
        report["readiness"] = "ready_except_network_or_skipped"
        report["next_steps"].append("Run with --probe-network to verify DGI connectivity")
        report["next_steps"].append("When network is OK, issue CFE and use --send")
    else:
        report["readiness"] = "blocked"
        if statuses.get("xsd_schema") != "ok":
            report["next_steps"].append("Restore official XSD package under compliance/dgi/evidence/xsd/")
        if statuses.get("certificate") not in {"ok"}:
            report["next_steps"].append(
                "Configure DGI_CERT_PATH / DGI_KEY_PATH with a valid ePrueba certificate (see docs/DGI_EPRUEBA_CHECKLIST.md)"
            )

    return report


async def send_test(fiscal_document_id: str) -> dict[str, Any]:
    from uuid import UUID

    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.fiscal_document import FiscalDocument
    from app.services.fiscal.engine import FiscalEngine, FiscalEngineError

    report: dict[str, Any] = {
        "timestamp": _utc_now(),
        "mode": "send",
        "fiscal_document_id": fiscal_document_id,
        "environment": settings.DGI_ENVIRONMENT,
        "endpoint": _endpoint_url(),
    }

    async with AsyncSessionLocal() as db:
        engine = FiscalEngine(db)
        try:
            stmt = select(FiscalDocument).where(FiscalDocument.id == UUID(fiscal_document_id))
            result = await db.execute(stmt)
            doc = result.scalar_one_or_none()
            if not doc:
                report["status"] = "error"
                report["error"] = "Fiscal document not found"
                return report

            if not (doc.raw_payload or {}).get("signed_xml"):
                report["status"] = "error"
                report["error"] = (
                    "Fiscal document has no signed_xml in raw_payload. "
                    "Emit (issue) the document first with a certificate."
                )
                return report

            response = await engine.send_cfe(
                fiscal_document_id=doc.id,
                tenant_id=doc.tenant_id,
                environment=settings.DGI_ENVIRONMENT,
            )
            await db.commit()
            report["status"] = "ok"
            report["dgi_response"] = response
        except FiscalEngineError as exc:
            report["status"] = "error"
            report["error"] = str(exc)
            await db.rollback()
        except Exception as exc:  # noqa: BLE001
            report["status"] = "error"
            report["error"] = f"{type(exc).__name__}: {exc}"
            await db.rollback()

    return report


def save_report(report: dict[str, Any], prefix: str = "eprueba") -> Path:
    out_dir = _test_cases_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"{prefix}_{ts}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="DGI ePrueba sandbox readiness / send")
    parser.add_argument("--dry-run", action="store_true", help="Check local prerequisites (default)")
    parser.add_argument("--probe-network", action="store_true", help="Also probe TLS to DGI endpoint")
    parser.add_argument("--send", action="store_true", help="Send an issued fiscal document to DGI")
    parser.add_argument("--fiscal-document-id", help="Fiscal document UUID for --send")
    args = parser.parse_args()

    if args.send:
        if not args.fiscal_document_id:
            parser.error("--fiscal-document-id is required with --send")
        report = asyncio.run(send_test(args.fiscal_document_id))
        prefix = "eprueba_send"
    else:
        report = dry_run(probe_network=args.probe_network)
        prefix = "eprueba_dryrun"

    path = save_report(report, prefix=prefix)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport saved to: {path}")

    if args.send:
        sys.exit(0 if report.get("status") == "ok" else 1)

    readiness = report.get("readiness")
    if readiness == "ready_for_live_send":
        sys.exit(0)
    if readiness == "ready_except_network_or_skipped":
        sys.exit(2)
    sys.exit(1)


if __name__ == "__main__":
    main()
