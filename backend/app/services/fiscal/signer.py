import base64
import structlog
from pathlib import Path
from typing import Optional

from cryptography import x509 as crypto_x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from lxml import etree

logger = structlog.get_logger(__name__)


class CertificateError(Exception):
    """Raised when certificate operations fail."""


class SigningError(Exception):
    """Raised when XML signing fails."""


def load_certificate(cert_path: str) -> tuple[crypto_x509.Certificate, bytes]:
    logger.info("loading_certificate", cert_path=cert_path)

    cert_file = Path(cert_path)
    if not cert_file.exists():
        raise CertificateError(f"Certificate file not found: {cert_path}")

    with open(cert_path, "rb") as f:
        cert_data = f.read()

    try:
        cert = crypto_x509.load_pem_x509_certificate(cert_data)
    except ValueError:
        try:
            cert = crypto_x509.load_der_x509_certificate(cert_data)
        except ValueError as e:
            raise CertificateError(f"Unable to parse certificate: {e}")

    logger.info(
        "certificate_loaded",
        subject=str(cert.subject),
        issuer=str(cert.issuer),
    )

    return cert, cert_data


def load_private_key(key_path: str, password: Optional[str] = None):
    logger.info("loading_private_key", key_path=key_path)

    key_file = Path(key_path)
    if not key_file.exists():
        raise CertificateError(f"Private key file not found: {key_path}")

    with open(key_path, "rb") as f:
        key_data = f.read()

    password_bytes = password.encode() if password else None

    try:
        private_key = serialization.load_pem_private_key(key_data, password=password_bytes)
    except ValueError:
        try:
            private_key = serialization.load_der_private_key(key_data, password=password_bytes)
        except ValueError as e:
            raise CertificateError(f"Unable to parse private key: {e}")

    return private_key


def sign_xml(
    xml_bytes: bytes,
    private_key,
    cert: crypto_x509.Certificate,
    cert_data: bytes,
) -> bytes:
    logger.info("signing_xml", xml_length=len(xml_bytes))

    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        raise SigningError(f"Invalid XML for signing: {e}")

    try:
        unsigned_root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        raise SigningError(f"Invalid XML for digest calculation: {e}")

    ds = "http://www.w3.org/2000/09/xmldsig#"
    sig = etree.SubElement(root, f"{{{ds}}}Signature")
    sig.set("Id", "Signature")

    signed_info = etree.SubElement(sig, f"{{{ds}}}SignedInfo")

    c14n = etree.SubElement(signed_info, f"{{{ds}}}CanonicalizationMethod")
    c14n.set("Algorithm", "http://www.w3.org/2001/10/xml-exc-c14n#")

    sig_method = etree.SubElement(signed_info, f"{{{ds}}}SignatureMethod")
    sig_method.set("Algorithm", "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256")

    reference = etree.SubElement(signed_info, f"{{{ds}}}Reference")
    reference.set("URI", "")

    transforms = etree.SubElement(reference, f"{{{ds}}}Transforms")
    t1 = etree.SubElement(transforms, f"{{{ds}}}Transform")
    t1.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")

    digest_method = etree.SubElement(reference, f"{{{ds}}}DigestMethod")
    digest_method.set("Algorithm", "http://www.w3.org/2001/04/xmlenc#sha256")

    digest_value = etree.SubElement(reference, f"{{{ds}}}DigestValue")

    doc_c14n = etree.tostring(unsigned_root, method="c14n", exclusive=True, with_comments=False)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(doc_c14n)
    digest_value.text = base64.b64encode(digest.finalize()).decode("utf-8")

    signed_info_elem = sig.find(f"{{{ds}}}SignedInfo")
    signed_info_bytes = etree.tostring(signed_info_elem, method="c14n", exclusive=True, with_comments=False)

    signature = private_key.sign(
        signed_info_bytes,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    sig_value = etree.SubElement(sig, f"{{{ds}}}SignatureValue")
    sig_value.text = base64.b64encode(signature).decode("utf-8")

    key_info = etree.SubElement(sig, f"{{{ds}}}KeyInfo")
    x509_data = etree.SubElement(key_info, f"{{{ds}}}X509Data")
    x509_cert = etree.SubElement(x509_data, f"{{{ds}}}X509Certificate")

    pem_text = cert_data.decode("utf-8", errors="replace")
    pem_body = pem_text.replace("-----BEGIN CERTIFICATE-----", "").replace("-----END CERTIFICATE-----", "").strip()
    x509_cert.text = pem_body

    signed_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    return signed_xml
