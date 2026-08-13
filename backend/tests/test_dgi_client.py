"""Unit tests for DGI SOAP client response parsing."""

import pytest
from lxml import etree

from app.services.fiscal.dgi_client import DGIClient, DGIError


def _soap_response(operation: str, body_xml: str) -> bytes:
  envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:ws="http://ws.efactura.dgi.gub.uy/">
  <soapenv:Body>
    <ws:{operation}Response>
      {body_xml}
    </ws:{operation}Response>
  </soapenv:Body>
</soapenv:Envelope>"""
  return envelope.encode("utf-8")


def test_parse_response_extracts_result_fields():
    client = DGIClient(environment="testing")
    root = etree.fromstring(
        _soap_response(
            "EFACRECEPCIONSOBRE",
            """
            <Resultado>
              <Estado>aceptado</Estado>
              <Mensaje>OK</Mensaje>
              <IdTransaccion>TX-123</IdTransaccion>
            </Resultado>
            """,
        )
    )

    parsed = client._parse_response(root, "EFACRECEPCIONSOBRE")

    assert parsed["status_code"] == "aceptado"
    assert parsed["status_message"] == "OK"
    assert parsed["response_id"] == "TX-123"


def test_parse_response_raises_on_soap_fault():
    client = DGIClient(environment="testing")
    fault_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <soapenv:Fault>
      <faultstring>Invalid request</faultstring>
      <detail>Bad envelope</detail>
    </soapenv:Fault>
  </soapenv:Body>
</soapenv:Envelope>"""
    root = etree.fromstring(fault_xml)

    with pytest.raises(DGIError, match="SOAP fault"):
        client._parse_response(root, "EFACRECEPCIONSOBRE")


def test_unsupported_environment_raises():
    with pytest.raises(DGIError, match="Unsupported DGI environment"):
        DGIClient(environment="invalid")
