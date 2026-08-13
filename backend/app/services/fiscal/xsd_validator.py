"""CFE XML validation against official XSD (when available) and structural checks."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import structlog
from lxml import etree

logger = structlog.get_logger(__name__)

CFE_NAMESPACE = "http://cfe.dgi.gub.uy"
DEFAULT_XSD_PATH = (
    Path(__file__).resolve().parents[4]
    / "compliance"
    / "dgi"
    / "evidence"
    / "xsd"
    / "CFEDGI.xsd"
)


class CFEValidationError(Exception):
    """Raised when CFE XML fails validation."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _structural_validate(xml_bytes: bytes) -> List[str]:
    errors: List[str] = []
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        return [f"XML mal formado: {exc}"]

    tag = etree.QName(root).localname
    ns = etree.QName(root).namespace
    if tag != "CFE":
        errors.append(f"Elemento raíz esperado CFE, encontrado {tag}")
    if ns != CFE_NAMESPACE:
        errors.append(f"Namespace esperado {CFE_NAMESPACE}, encontrado {ns or 'ninguno'}")

    body = None
    for body_name in ("eFact", "eTck"):
        body = root.find(f"{{{CFE_NAMESPACE}}}{body_name}")
        if body is None:
            body = root.find(body_name)
        if body is not None:
            break
    if body is None:
        errors.append("Elemento obligatorio faltante: eFact o eTck")
        return errors

    for child_name in ("TmstFirma", "Encabezado", "Detalle", "CAEData"):
        child = body.find(f"{{{CFE_NAMESPACE}}}{child_name}")
        if child is None:
            child = body.find(child_name)
        if child is None:
            errors.append(f"Elemento obligatorio faltante: {child_name}")

    encabezado = body.find(f"{{{CFE_NAMESPACE}}}Encabezado")
    if encabezado is None:
        encabezado = body.find("Encabezado")
    if encabezado is not None:
        for child_name in ("IdDoc", "Emisor", "Totales"):
            child = encabezado.find(f"{{{CFE_NAMESPACE}}}{child_name}")
            if child is None:
                child = encabezado.find(child_name)
            if child is None:
                errors.append(f"Elemento obligatorio faltante: Encabezado/{child_name}")

    return errors


def _xsd_validate(xml_bytes: bytes, xsd_path: Path) -> List[str]:
    try:
        import xmlschema
    except ImportError:
        return ["xmlschema no está instalado"]

    if not xsd_path.exists():
        return [f"XSD no encontrado: {xsd_path}"]

    try:
        schema = xmlschema.XMLSchema(str(xsd_path))
        schema.validate(xml_bytes)
        return []
    except xmlschema.XMLSchemaException as exc:
        return [f"Error al cargar XSD: {exc}"]
    except xmlschema.XMLSchemaValidationError as exc:
        return [f"Validación XSD fallida: {exc}"]


def validate_cfe_xml(
    xml_bytes: bytes,
    *,
    xsd_path: Optional[Path] = None,
    require_xsd: bool = False,
    validate_xsd: bool = True,
) -> List[str]:
    """
    Validate CFE XML. Always runs structural checks.
    XSD validation runs when validate_xsd=True and the schema file exists.
    Unsigned XML will fail full XSD validation because ds:Signature is required.
    """
    errors = _structural_validate(xml_bytes)
    if errors or not validate_xsd:
        return errors

    path = xsd_path or DEFAULT_XSD_PATH
    if path.exists():
        errors.extend(_xsd_validate(xml_bytes, path))
    elif require_xsd:
        errors.append(
            f"XSD obligatorio no encontrado en {path}. "
            "Descargar desde https://www.efactura.dgi.gub.uy/principal/ampliacion_de_contenido/documentos-de-interes"
        )
    else:
        logger.warning("cfe_xsd_validation_skipped", path=str(path), reason="xsd_not_found")

    return errors


def validate_cfe_xml_or_raise(
    xml_bytes: bytes,
    *,
    xsd_path: Optional[Path] = None,
    require_xsd: bool = False,
    validate_xsd: bool = True,
) -> None:
    errors = validate_cfe_xml(
        xml_bytes,
        xsd_path=xsd_path,
        require_xsd=require_xsd,
        validate_xsd=validate_xsd,
    )
    if errors:
        raise CFEValidationError(errors)
