import structlog
import base64
from typing import Optional
from lxml import etree

logger = structlog.get_logger(__name__)


SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
WSSE_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
WSU_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
DS_NS = "http://www.w3.org/2000/09/xmldsig#"


def build_soap_envelope(
    operation: str,
    payload: bytes,
    certificate_data: Optional[bytes] = None,
    request_id: Optional[str] = None,
) -> bytes:
    logger.info(
        "building_soap_envelope",
        operation=operation,
        payload_length=len(payload),
        request_id=request_id,
    )

    envelope = etree.Element(f"{{{SOAP_NS}}}Envelope", nsmap={
        "soapenv": SOAP_NS,
        "wsse": WSSE_NS,
        "wsu": WSU_NS,
        "ds": DS_NS,
    })

    header = etree.SubElement(envelope, f"{{{SOAP_NS}}}Header")

    security = etree.SubElement(header, f"{{{WSSE_NS}}}Security")
    security.set("{http://schemas.xmlsoap.org/soap/envelope/}mustUnderstand", "1")

    if certificate_data:
        token = etree.SubElement(
            security,
            f"{{{WSSE_NS}}}BinarySecurityToken",
        )
        token.set("EncodingType", "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary")
        token.set("ValueType", "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3")
        if request_id:
            token.set(f"{{{WSU_NS}}}Id", f"X509Token-{request_id}")
        else:
            token.set(f"{{{WSU_NS}}}Id", "X509Token")

        pem_text = certificate_data.decode("utf-8", errors="replace")
        pem_body = pem_text.replace("-----BEGIN CERTIFICATE-----", "").replace("-----END CERTIFICATE-----", "").strip()
        token.text = pem_body

    body = etree.SubElement(envelope, f"{{{SOAP_NS}}}Body")

    payload_b64 = base64.b64encode(payload).decode("utf-8")

    if operation == "EFACRECEPCIONSOBRE":
        op_elem = etree.SubElement(body, f"{{http://ws.efactura.dgi.gub.uy/}}EFACRECEPCIONSOBRE")
    elif operation == "EFACCONSULTARESTADOENVIO":
        op_elem = etree.SubElement(body, f"{{http://ws.efactura.dgi.gub.uy/}}EFACCONSULTARESTADOENVIO")
    elif operation == "EFACCONSULTARESTADOCFE":
        op_elem = etree.SubElement(body, f"{{http://ws.efactura.dgi.gub.uy/}}EFACCONSULTARESTADOCFE")
    elif operation == "EFACRECEPCIONREPORTE":
        op_elem = etree.SubElement(body, f"{{http://ws.efactura.dgi.gub.uy/}}EFACRECEPCIONREPORTE")
    elif operation == "EFACSOLACTUALIZARCONTACTO":
        op_elem = etree.SubElement(body, f"{{http://ws.efactura.dgi.gub.uy/}}EFACSOLACTUALIZARCONTACTO")
    else:
        op_elem = etree.SubElement(body, f"{{http://ws.efactura.dgi.gub.uy/}}{operation}")

    xml_sobre = etree.SubElement(op_elem, "XmlSOBRE")
    xml_sobre.text = payload_b64

    soap_bytes = etree.tostring(envelope, xml_declaration=True, encoding="UTF-8")
    return soap_bytes
