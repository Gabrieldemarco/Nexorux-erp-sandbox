# DGI Compliance Matrix

This document maps NEXORUX ERP's fiscal implementation to DGI (Dirección General Impositiva) requirements for electronic invoicing in Uruguay.

**Status legend:**

| Status | Meaning |
|--------|---------|
| `NOT_STARTED` | No work done |
| `IMPLEMENTED` | Code exists in the repository |
| `TESTED` | Covered by automated tests (may use mocks) |
| `NEEDS_DGI_CONFIRMATION` | Requires validation against official DGI documentation or sandbox |
| `VERIFIED` | Confirmed against official DGI documentation or sandbox |
| `HOMOLOGATED` | Officially approved by DGI |

> **This system is NOT homologated or approved by DGI.**

---

## CFE Document Types

| CFE Type | Code | Description | Code Status | DGI Status |
|----------|------|-------------|-------------|------------|
| e-Ticket | 101 | Electronic ticket for consumers | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| Nota de Crédito e-Ticket | 102 | Credit note on e-Ticket | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| Nota de Débito e-Ticket | 103 | Debit note on e-Ticket | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| e-Factura | 111 | Electronic invoice for companies | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| Nota de Crédito e-Factura | 112 | Credit note on e-Factura | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| Nota de Débito e-Factura | 113 | Debit note on e-Factura | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| e-Ticket Contingencia | 201 | Contingency ticket | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| Nota de Crédito e-Ticket Contingencia | 202 | Credit note on contingency ticket | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| Nota de Débito e-Ticket Contingencia | 203 | Debit note on contingency ticket | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| e-Factura Contingencia | 211 | Contingency invoice | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| Nota de Crédito e-Factura Contingencia | 212 | Credit note on contingency invoice | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |
| Nota de Débito e-Factura Contingencia | 213 | Debit note on contingency invoice | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION |

---

## Workflow Compliance

| Workflow | Code Status | DGI Status | Notes |
|----------|-------------|------------|-------|
| Issue (XML + sign) | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | Structural + XSD validation post-sign |
| Send (SOAP → DGI WS) | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | Mocked in tests |
| Query status | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | Mocked in tests |
| Retry rejected | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | State machine in place |
| Async send (Celery) | IMPLEMENTED | NEEDS_DGI_CONFIRMATION | Single task |
| Credit/debit note references | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | Via `invoice.metadata_json` |

---

## Environments

| Environment | Endpoint | Code Status | DGI Status |
|-------------|----------|-------------|------------|
| testing | `https://efactura.dgi.gub.uy:6443/ePrueba/ws_eprueba` | IMPLEMENTED | IN_PROGRESS (readiness script + checklist; live send needs cert) |
| homologacion | `https://efactura.dgi.gub.uy:6443/eHomologacion/ws_ehomologacion` | IMPLEMENTED | NOT_STARTED |
| produccion | `https://efactura.dgi.gub.uy:6443/eFactura/ws_efactura` | IMPLEMENTED | NOT_STARTED |

---

## Technical Requirements

| Requirement | Code Status | DGI Status | Evidence |
|-------------|-------------|------------|----------|
| XML per official XSD | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | `CFEDGI.xsd` + tests post-firma |
| Digital signature (X.509) | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | `signer.py` + XSD tests |
| SOAP envelope (WS-Security) | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | `soap_envelope.py` |
| Certificate management | IMPLEMENTED | NEEDS_DGI_CONFIRMATION | — |
| TLS 1.2+ for DGI comms | IMPLEMENTED | NEEDS_DGI_CONFIRMATION | — |
| Fiscal numbering (series/number) | IMPLEMENTED | NEEDS_DGI_CONFIRMATION | — |
| Contingency regime | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | Types 201–203, 211–213 |
| Response code parsing | IMPLEMENTED, TESTED | NEEDS_DGI_CONFIRMATION | `test_dgi_client.py` |
| Document retention | NOT_STARTED | NOT_STARTED | — |
| Official homologation | NOT_STARTED | NOT_STARTED | — |

---

## Compliance Evidence

| Artifact | Location | Status |
|----------|----------|--------|
| Discovery notes | `DGI_DISCOVERY.md` | Partial |
| Requirements | `compliance/dgi/requirements.md` | DONE |
| Compliance README | `compliance/dgi/README.md` | DONE |
| Official docs / XSD | `compliance/dgi/evidence/xsd/` | DONE (XSDs_FE v1.44.2) |
| CFE format PDF | `compliance/dgi/evidence/Formato_CFE_v25-2.pdf` | DONE |
| Test cases | `compliance/dgi/test-cases/` | DONE (dry-run reports) |
| ePrueba script | `backend/scripts/dgi_eprueba_test.py` | DONE (dry-run) |
| Unit tests | `backend/tests/test_xml_builder.py` | DONE (all primary CFE types + XSD) |
| Sandbox test results | `compliance/dgi/test-cases/` | NOT_STARTED (live send) |

---

## Next Steps for DGI Certification

1. Obtain test certificate from DGI
2. Run first CFE in ePrueba: `backend/scripts/dgi_eprueba_test.py --send --fiscal-document-id <uuid>`
3. Document request/response pairs in `compliance/dgi/test-cases/`
4. Request homologation access from DGI
5. Execute official homologation test suite
6. Do not declare production-ready until DGI approval

---

## References

- [DGI Portal](https://www.gub.uy/dgi)
- [DGI e-Factura](http://www.efactura.dgi.gub.uy/)
- [Uruguayan Fiscal Law 19132](https://www.impo.com.uy)
