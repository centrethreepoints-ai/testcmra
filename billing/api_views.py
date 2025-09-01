"""
API views for billing application.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import CreditNote, Invoice


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def credit_note_fetch(request, pk):
    """Return essential details of a credit note (avoir)."""
    cn = get_object_or_404(CreditNote, pk=pk, company=request.user.company)
    data = {
        "id": cn.id,
        "number": cn.number,
        "issue_date": cn.issue_date,
        "status": cn.status,
        "party_id": cn.party_id,
        "total_ht": str(cn.total_ht or 0),
        "total_tva": str(cn.total_tva or 0),
        "total_ttc": str(cn.total_ttc or 0),
        "credit_type": cn.credit_type,
        "original_invoice_id": cn.original_invoice_id,
        "reason": cn.reason,
    }
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_for_credit_note_fetch(request, pk):
    """Return invoice info to prefill a new credit note (avoir)."""
    invoice = get_object_or_404(Invoice, pk=pk, company=request.user.company)
    lines = []
    for ln in invoice.lines.all().select_related("product", "tax_rate"):
        lines.append(
            {
                "product_id": ln.product_id,
                "description": ln.description,
                "quantity": ln.quantity,
                "unit_price_ht": str(ln.unit_price_ht),
                "discount_percent": str(ln.discount_percent),
                "tax_rate_id": ln.tax_rate_id,
                "total_line_ht": str(ln.total_line_ht),
                "total_line_tva": str(ln.total_line_tva),
                "total_line_ttc": str(ln.total_line_ttc),
            }
        )

    data = {
        "invoice_id": invoice.id,
        "invoice_number": invoice.number,
        "party_id": invoice.party_id,
        "currency": invoice.currency,
        "discount_percent": str(invoice.discount_percent or 0),
        "withholding_tax_percent": str(invoice.withholding_tax_percent or 0),
        "notes": invoice.notes or "",
        "terms": invoice.terms or "",
        "totals": {
            "total_ht": str(invoice.total_ht or 0),
            "total_tva": str(invoice.total_tva or 0),
            "total_ttc": str(invoice.total_ttc or 0),
        },
        "lines": lines,
    }
    return Response(data)


