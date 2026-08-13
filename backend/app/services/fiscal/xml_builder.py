import re
import structlog
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, time, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from lxml import etree

from app.services.fiscal.cfe_types import CFEType, CFE_TYPE_INFO, is_note

logger = structlog.get_logger(__name__)

CFE_NAMESPACE = "http://cfe.dgi.gub.uy"
UY_TZ = timezone(timedelta(hours=-3))
BASIC_VAT_RATE = Decimal("22.000")
MIN_VAT_RATE = Decimal("10.000")

FACT_TYPES = {
    CFEType.E_FACTURA,
    CFEType.NOTA_CREDITO_E_FACTURA,
    CFEType.NOTA_DEBITO_E_FACTURA,
    CFEType.E_FACTURA_CONTINGENCIA,
    CFEType.NOTA_CREDITO_E_FACTURA_CONTINGENCIA,
    CFEType.NOTA_DEBITO_E_FACTURA_CONTINGENCIA,
}
TICKET_TYPES = {
    CFEType.E_TICKET,
    CFEType.NOTA_CREDITO_E_TICKET,
    CFEType.NOTA_DEBITO_E_TICKET,
    CFEType.E_TICKET_CONTINGENCIA,
    CFEType.NOTA_CREDITO_E_TICKET_CONTINGENCIA,
    CFEType.NOTA_DEBITO_E_TICKET_CONTINGENCIA,
}


def _decimal_to_str(value: Optional[Decimal], places: int = 2) -> str:
    if value is None:
        value = Decimal("0")
    quant = Decimal("1").scaleb(-places)
    return f"{value.quantize(quant, rounding=ROUND_HALF_UP):.{places}f}"


def _format_date(value: Optional[date]) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")


def _format_timestamp(value: Optional[date], issue_datetime: Optional[datetime] = None) -> str:
    if issue_datetime is not None:
        if issue_datetime.tzinfo is None:
            dt = issue_datetime.replace(tzinfo=UY_TZ)
        else:
            dt = issue_datetime.astimezone(UY_TZ)
    else:
        dt = datetime.combine(value or date.today(), time(12, 0, 0), tzinfo=UY_TZ)
    formatted = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    return formatted[:-2] + ":" + formatted[-2:]


def _cfe_code(document_type: str) -> str:
    value = getattr(document_type, "value", document_type)
    return str(value)


FACT_TYPE_CODES = {_cfe_code(t) for t in FACT_TYPES}
TICKET_TYPE_CODES = {_cfe_code(t) for t in TICKET_TYPES}


def _sub(parent: etree._Element, tag: str, text: Any = None) -> etree._Element:
    elem = etree.SubElement(parent, tag)
    if text is not None:
        elem.text = str(text)
    return elem


def _parse_series_number(
    series: Optional[str],
    number: Optional[str],
    cfe_number: Optional[str] = None,
) -> Tuple[str, int]:
    if series and number:
        serie = series.strip().upper()
        nro = int(str(number).lstrip("0") or "0")
        return serie, nro

    if not cfe_number:
        raise ValueError("CFE series/number is required")

    match = re.match(r"^([A-Z]{1,2})(\d+)$", cfe_number.strip().upper())
    if not match:
        raise ValueError(f"Invalid CFE number format: {cfe_number}")
    return match.group(1), int(match.group(2))


def _normalize_rut(rut: str) -> str:
    digits = re.sub(r"\D", "", rut or "")
    if len(digits) != 12:
        raise ValueError(f"RUT must have 12 digits, got {len(digits)}")
    return digits


def _item_line_net(item) -> Decimal:
    qty = Decimal(str(item.quantity))
    unit = Decimal(str(item.unit_price))
    discount = Decimal(str(getattr(item, "discount", 0) or 0))
    return qty * unit - discount


def _item_tax_amount(item) -> Decimal:
    return Decimal(str(getattr(item, "tax_amount", 0) or 0))


def _item_ind_fact(item) -> str:
    line_net = _item_line_net(item)
    tax = _item_tax_amount(item)
    if line_net <= 0:
        return "1"
    rate = tax / line_net
    if rate >= Decimal("0.20"):
        return "3"
    if rate >= Decimal("0.08"):
        return "2"
    if tax > 0:
        return "4"
    return "1"


def _aggregate_totals(items: List) -> Dict[str, Decimal]:
    mnt_no_grv = Decimal("0")
    mnt_neto_min = Decimal("0")
    mnt_neto_basica = Decimal("0")
    mnt_neto_otra = Decimal("0")
    mnt_iva_min = Decimal("0")
    mnt_iva_basica = Decimal("0")
    mnt_iva_otra = Decimal("0")

    for item in items:
        line_net = _item_line_net(item)
        tax = _item_tax_amount(item)
        ind = _item_ind_fact(item)
        if ind == "1":
            mnt_no_grv += line_net
        elif ind == "2":
            mnt_neto_min += line_net
            mnt_iva_min += tax
        elif ind == "3":
            mnt_neto_basica += line_net
            mnt_iva_basica += tax
        else:
            mnt_neto_otra += line_net
            mnt_iva_otra += tax

    mnt_total = mnt_no_grv + mnt_neto_min + mnt_neto_basica + mnt_neto_otra + mnt_iva_min + mnt_iva_basica + mnt_iva_otra

    return {
        "mnt_no_grv": mnt_no_grv,
        "mnt_neto_min": mnt_neto_min,
        "mnt_neto_basica": mnt_neto_basica,
        "mnt_neto_otra": mnt_neto_otra,
        "mnt_iva_min": mnt_iva_min,
        "mnt_iva_basica": mnt_iva_basica,
        "mnt_iva_otra": mnt_iva_otra,
        "mnt_total": mnt_total,
        "mnt_pagar": mnt_total,
        "cant_lin_det": len(items),
    }


def _resolve_cae_data(company, invoice, cae_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if cae_data:
        return cae_data

    metadata = getattr(invoice, "metadata_json", None) or {}
    if isinstance(metadata, dict) and metadata.get("cae_data"):
        return metadata["cae_data"]

    company_meta = getattr(company, "metadata_json", None) or {}
    if isinstance(company_meta, dict) and company_meta.get("cae_data"):
        return company_meta["cae_data"]

    return {
        "cae_id": getattr(company, "cae_id", 90000000001),
        "d_nro": 1,
        "h_nro": 9999999,
        "fec_venc": date.today().replace(year=date.today().year + 1),
    }


def _build_id_doc(
    encabezado: etree._Element,
    document_type: str,
    serie: str,
    nro: int,
    issue_date: date,
    payment_method: int = 1,
    notes: Optional[str] = None,
) -> None:
    id_doc = _sub(encabezado, "IdDoc")
    _sub(id_doc, "TipoCFE", _cfe_code(document_type))
    _sub(id_doc, "Serie", serie)
    _sub(id_doc, "Nro", nro)
    _sub(id_doc, "FchEmis", _format_date(issue_date))
    _sub(id_doc, "FmaPago", payment_method)
    if notes:
        _sub(id_doc, "InfoAdicionalDoc", notes[:1000])


def _build_emisor(encabezado: etree._Element, company) -> None:
    emisor = _sub(encabezado, "Emisor")
    _sub(emisor, "RUCEmisor", _normalize_rut(company.rut))
    _sub(emisor, "RznSoc", company.legal_name[:150])

    trade_name = getattr(company, "trade_name", None)
    if trade_name:
        _sub(emisor, "NomComercial", trade_name[:30])

    giro = getattr(company, "business_activity", None) or getattr(company, "tax_regime", None) or "Comercio"
    _sub(emisor, "GiroEmis", str(giro)[:100])

    phone = getattr(company, "phone", None)
    if phone:
        _sub(emisor, "Telefono", str(phone)[:20])

    email = getattr(company, "email", None)
    if email:
        _sub(emisor, "CorreoEmisor", str(email)[:80])

    branch_code = getattr(company, "dgi_branch_code", None)
    if branch_code is None:
        meta = getattr(company, "metadata_json", None) or {}
        if isinstance(meta, dict):
            branch_code = meta.get("dgi_branch_code", 1)
        else:
            branch_code = 1
    _sub(emisor, "CdgDGISucur", int(branch_code))

    fiscal_address = getattr(company, "fiscal_address", None) or "Sin especificar"
    _sub(emisor, "DomFiscal", str(fiscal_address)[:70])

    city = getattr(company, "locality", None) or getattr(company, "city", None) or "Montevideo"
    _sub(emisor, "Ciudad", str(city)[:30])

    department = getattr(company, "department", None) or "Montevideo"
    _sub(emisor, "Departamento", str(department)[:30])


def _build_receptor_fact(encabezado: etree._Element, customer) -> None:
    receptor = _sub(encabezado, "Receptor")
    if customer and getattr(customer, "rut", None):
        _sub(receptor, "TipoDocRecep", 2)
        _sub(receptor, "CodPaisRecep", "UY")
        _sub(receptor, "DocRecep", _normalize_rut(customer.rut))
    if customer and getattr(customer, "legal_name", None):
        _sub(receptor, "RznSocRecep", customer.legal_name[:150])
    if customer and getattr(customer, "address", None):
        _sub(receptor, "DirRecep", str(customer.address)[:70])


def _build_receptor_tck(encabezado: etree._Element, customer) -> None:
    if not customer:
        return
    receptor = _sub(encabezado, "Receptor")
    if getattr(customer, "rut", None):
        _sub(receptor, "TipoDocRecep", 2)
        _sub(receptor, "CodPaisRecep", "UY")
        _sub(receptor, "DocRecep", _normalize_rut(customer.rut))
    if getattr(customer, "legal_name", None):
        _sub(receptor, "RznSocRecep", customer.legal_name[:150])
    if getattr(customer, "address", None):
        _sub(receptor, "DirRecep", str(customer.address)[:70])


def _build_totales(encabezado: etree._Element, totals: Dict[str, Decimal], currency: str, exchange_rate: Decimal) -> None:
    totales = _sub(encabezado, "Totales")
    _sub(totales, "TpoMoneda", currency)
    if currency != "UYU" and exchange_rate and exchange_rate != 1:
        _sub(totales, "TpoCambio", _decimal_to_str(exchange_rate, 4))

    if totals["mnt_no_grv"] > 0:
        _sub(totales, "MntNoGrv", _decimal_to_str(totals["mnt_no_grv"]))
    if totals["mnt_neto_min"] > 0:
        _sub(totales, "MntNetoIvaTasaMin", _decimal_to_str(totals["mnt_neto_min"]))
        _sub(totales, "IVATasaMin", _decimal_to_str(MIN_VAT_RATE, 3))
        _sub(totales, "MntIVATasaMin", _decimal_to_str(totals["mnt_iva_min"]))
    if totals["mnt_neto_basica"] > 0:
        _sub(totales, "MntNetoIVATasaBasica", _decimal_to_str(totals["mnt_neto_basica"]))
        _sub(totales, "IVATasaBasica", _decimal_to_str(BASIC_VAT_RATE, 3))
        _sub(totales, "MntIVATasaBasica", _decimal_to_str(totals["mnt_iva_basica"]))
    if totals["mnt_neto_otra"] > 0:
        _sub(totales, "MntNetoIVAOtra", _decimal_to_str(totals["mnt_neto_otra"]))
        _sub(totales, "MntIVAOtra", _decimal_to_str(totals["mnt_iva_otra"]))

    _sub(totales, "MntTotal", _decimal_to_str(totals["mnt_total"]))
    _sub(totales, "CantLinDet", totals["cant_lin_det"])
    _sub(totales, "MntPagar", _decimal_to_str(totals["mnt_pagar"]))


def _build_detalle(cfe_body: etree._Element, items: List) -> None:
    detalle = _sub(cfe_body, "Detalle")
    for idx, item in enumerate(items, 1):
        item_elem = _sub(detalle, "Item")
        _sub(item_elem, "NroLinDet", idx)
        _sub(item_elem, "IndFact", _item_ind_fact(item))
        description = getattr(item, "description", None) or f"Item {idx}"
        _sub(item_elem, "NomItem", str(description)[:80])
        _sub(item_elem, "Cantidad", _decimal_to_str(Decimal(str(item.quantity)), 3))
        _sub(item_elem, "UniMed", "N/A")
        _sub(item_elem, "PrecioUnitario", _decimal_to_str(Decimal(str(item.unit_price)), 6))
        discount = Decimal(str(getattr(item, "discount", 0) or 0))
        if discount > 0:
            _sub(item_elem, "DescuentoMonto", _decimal_to_str(discount))
        line_net = _item_line_net(item)
        _sub(item_elem, "MontoItem", _decimal_to_str(line_net))


def _build_referencia(cfe_body: etree._Element, reference_document: Dict[str, Any]) -> None:
    # XSD order: NroLinRef, IndGlobal?, TpoDocRef?, Serie?, NroCFERef?, RazonRef?, FechaCFEref?, ...
    ref_root = _sub(cfe_body, "Referencia")
    ref = _sub(ref_root, "Referencia")
    _sub(ref, "NroLinRef", 1)
    _sub(ref, "TpoDocRef", _cfe_code(reference_document.get("document_type", "")))
    serie, nro = _parse_series_number(
        reference_document.get("series"),
        reference_document.get("number"),
        reference_document.get("cfe_number"),
    )
    _sub(ref, "Serie", serie)
    _sub(ref, "NroCFERef", nro)
    reason = reference_document.get("reason")
    if reason:
        _sub(ref, "RazonRef", str(reason)[:90])
    issue_date = reference_document.get("issue_date")
    if issue_date:
        _sub(ref, "FechaCFEref", _format_date(issue_date))


def _build_cae_data(cfe_body: etree._Element, cae_data: Dict[str, Any]) -> None:
    cae = _sub(cfe_body, "CAEData")
    _sub(cae, "CAE_ID", int(cae_data["cae_id"]))
    _sub(cae, "DNro", int(cae_data["d_nro"]))
    _sub(cae, "HNro", int(cae_data["h_nro"]))
    fec_venc = cae_data.get("fec_venc")
    if isinstance(fec_venc, datetime):
        fec_venc = fec_venc.date()
    elif isinstance(fec_venc, str):
        fec_venc = date.fromisoformat(fec_venc[:10])
    _sub(cae, "FecVenc", _format_date(fec_venc))


def build_cfe_xml(
    invoice,
    company,
    customer,
    items,
    document_type: str,
    cfe_number: str,
    issue_date: date,
    currency: str = "UYU",
    exchange_rate: Decimal = Decimal("1"),
    notes: Optional[str] = None,
    reference_document: Optional[Dict[str, Any]] = None,
    cae_data: Optional[Dict[str, Any]] = None,
    payment_method: int = 1,
) -> bytes:
    logger.info(
        "building_cfe_xml",
        document_type=document_type,
        cfe_number=cfe_number,
        invoice_id=str(invoice.id),
    )

    cfe_type_info = CFE_TYPE_INFO.get(document_type)
    if not cfe_type_info:
        raise ValueError(f"Unsupported CFE type: {document_type}")

    requires_rut = cfe_type_info["requires_receptor_rut"]

    if not company or not company.rut:
        raise ValueError("Company RUT is required to build a CFE")
    if not items:
        raise ValueError("At least one invoice item is required to build a CFE")
    if requires_rut and (not customer or not getattr(customer, "rut", None)):
        raise ValueError("Customer RUT is required for this CFE type")
    if is_note(document_type) and not reference_document:
        raise ValueError("Reference document is required for credit and debit notes")
    if currency != "UYU" and (exchange_rate is None or exchange_rate <= 0):
        raise ValueError("Exchange rate must be greater than zero for foreign currency CFEs")

    serie, nro = _parse_series_number(
        getattr(invoice, "series", None),
        getattr(invoice, "number", None),
        cfe_number,
    )
    totals = _aggregate_totals(items)
    resolved_cae = _resolve_cae_data(company, invoice, cae_data)
    issue_datetime = getattr(invoice, "issue_date", None)

    root = etree.Element("CFE", nsmap={None: CFE_NAMESPACE})
    root.set("version", "1.0")

    doc_code = _cfe_code(document_type)

    if doc_code in TICKET_TYPE_CODES:
        cfe_body = _sub(root, "eTck")
    elif doc_code in FACT_TYPE_CODES:
        cfe_body = _sub(root, "eFact")
    else:
        raise ValueError(f"Unsupported CFE type for XML builder: {document_type}")

    _sub(cfe_body, "TmstFirma", _format_timestamp(issue_date, issue_datetime))

    encabezado = _sub(cfe_body, "Encabezado")
    _build_id_doc(encabezado, doc_code, serie, nro, issue_date, payment_method, notes)
    _build_emisor(encabezado, company)

    if doc_code in FACT_TYPE_CODES:
        _build_receptor_fact(encabezado, customer)
    else:
        _build_receptor_tck(encabezado, customer)

    _build_totales(encabezado, totals, currency, Decimal(str(exchange_rate)))
    _build_detalle(cfe_body, items)

    if is_note(document_type) and reference_document:
        _build_referencia(cfe_body, reference_document)

    _build_cae_data(cfe_body, resolved_cae)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)
