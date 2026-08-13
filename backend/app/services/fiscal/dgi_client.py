import structlog
import httpx
import base64
from typing import Optional, Dict, Any
from lxml import etree

from app.core.config import settings
from app.services.fiscal.soap_envelope import build_soap_envelope

logger = structlog.get_logger(__name__)


DGI_ENDPOINTS: Dict[str, Dict[str, str]] = {
    "testing": {
        "url": "https://efactura.dgi.gub.uy:6443/ePrueba/ws_eprueba",
        "namespace": "http://ws.int.efactura.dgi.gub.uy/",
    },
    "homologacion": {
        "url": "https://efactura.dgi.gub.uy:6443/eHomologacion/ws_ehomologacion",
        "namespace": "http://ws.efactura.dgi.gub.uy/",
    },
    "produccion": {
        "url": "https://efactura.dgi.gub.uy:6443/eFactura/ws_efactura",
        "namespace": "http://ws.efactura.dgi.gub.uy/",
    },
}


class DGIError(Exception):
    """Base exception for DGI client errors."""

    def __init__(self, message: str, status_code: Optional[str] = None, raw_response: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.raw_response = raw_response


class DGIClient:
    """Async SOAP client for DGI web services."""

    def __init__(self, environment: str = "testing", certificate_data: Optional[bytes] = None):
        env_config = DGI_ENDPOINTS.get(environment)
        if env_config is None:
            raise DGIError(f"Unsupported DGI environment: {environment}")
        self.url = env_config["url"]
        self.namespace = env_config["namespace"]
        self.certificate_data = certificate_data
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                verify=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def send_operation(
        self,
        operation: str,
        payload: bytes,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info(
            "dgi_send_operation",
            operation=operation,
            url=self.url,
            request_id=request_id,
        )

        soap_envelope = build_soap_envelope(
            operation=operation,
            payload=payload,
            certificate_data=self.certificate_data,
            request_id=request_id,
        )

        client = await self._get_client()
        headers = {
            "Content-Type": 'text/xml; charset="utf-8"',
            "SOAPAction": f'"{self.namespace}{operation}"',
        }

        try:
            response = await client.post(self.url, content=soap_envelope, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("dgi_http_error", status_code=e.response.status_code, response_text=e.response.text[:500])
            raise DGIError(
                f"HTTP error {e.response.status_code}",
                status_code=str(e.response.status_code),
                raw_response=e.response.text[:2000],
            )
        except httpx.RequestError as e:
            logger.error("dgi_request_error", error=str(e))
            raise DGIError(f"Request error: {e}")

        response_text = response.text
        logger.info("dgi_response_received", response_length=len(response_text))

        try:
            root = etree.fromstring(response_text.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            logger.error("dgi_response_parse_error", error=str(e))
            raise DGIError(f"Invalid SOAP response: {e}", raw_response=response_text[:2000])

        return self._parse_response(root, operation)

    def _parse_response(self, root: etree.Element, operation: str) -> Dict[str, Any]:
        body = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")
        if body is None:
            raise DGIError("SOAP body not found in response")

        fault = body.find("{http://schemas.xmlsoap.org/soap/envelope/}Fault")
        if fault is not None:
            fault_string = fault.find("faultstring")
            detail = fault.find("detail")
            error_msg = fault_string.text if fault_string is not None else "Unknown SOAP fault"
            error_detail = detail.text if detail is not None else ""
            logger.error("dgi_soap_fault", error=error_msg, detail=error_detail[:500])
            raise DGIError(f"SOAP fault: {error_msg}", raw_response=error_detail[:2000])

        response_elem = body.find(f"{{http://ws.efactura.dgi.gub.uy/}}{operation}Response")
        if response_elem is None:
            response_elem = body.find(f"{{{self.namespace}}}{operation}Response")

        if response_elem is None:
            raise DGIError(f"Response element for {operation} not found")

        result_elem = response_elem.find(".//Resultado")
        if result_elem is None:
            return {"raw": etree.tostring(response_elem, encoding="unicode")}

        status_code = result_elem.findtext("Estado")
        status_message = result_elem.findtext("Mensaje")
        response_id = result_elem.findtext("IdTransaccion") or result_elem.findtext("IDTransaccion")
        raw_xml = etree.tostring(result_elem, encoding="unicode")

        return {
            "status_code": status_code,
            "status_message": status_message,
            "response_id": response_id,
            "raw_response": raw_xml,
        }

    async def send_cfe_envelope(self, signed_cfe_xml: bytes, request_id: Optional[str] = None) -> Dict[str, Any]:
        return await self.send_operation("EFACRECEPCIONSOBRE", signed_cfe_xml, request_id)

    async def query_envelope_status(self, request_id: str) -> Dict[str, Any]:
        logger.info("querying_envelope_status", request_id=request_id)
        payload = f"<IdTransaccion>{request_id}</IdTransaccion>".encode("utf-8")
        return await self.send_operation("EFACCONSULTARESTADOENVIO", payload)

    async def query_cfe_status(self, rut: str, cfe_type: str, cfe_number: str, issue_date: str) -> Dict[str, Any]:
        logger.info("querying_cfe_status", rut=rut, cfe_type=cfe_type, cfe_number=cfe_number)
        payload = f"""
        <ConsultaCFE>
            <Rut>{rut}</Rut>
            <TipoCFE>{cfe_type}</TipoCFE>
            <NumeroCFE>{cfe_number}</NumeroCFE>
            <FechaEmision>{issue_date}</FechaEmision>
        </ConsultaCFE>
        """.strip().encode("utf-8")
        return await self.send_operation("EFACCONSULTARESTADOCFE", payload)

    async def send_daily_report(self, report_xml: bytes, request_id: Optional[str] = None) -> Dict[str, Any]:
        return await self.send_operation("EFACRECEPCIONREPORTE", report_xml, request_id)

    async def update_contact(self, rut: str, email: str, phone: Optional[str] = None) -> Dict[str, Any]:
        logger.info("updating_contact", rut=rut, email=email)
        payload = f"""
        <ActualizaContacto>
            <Rut>{rut}</Rut>
            <Correo>{email}</Correo>
            <Telefono>{phone or ''}</Telefono>
        </ActualizaContacto>
        """.strip().encode("utf-8")
        return await self.send_operation("EFACSOLACTUALIZARCONTACTO", payload)
