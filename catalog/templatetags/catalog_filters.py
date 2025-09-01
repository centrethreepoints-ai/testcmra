from decimal import Decimal, ROUND_HALF_UP

from django import template


register = template.Library()


@register.filter(name="ttc")
def ttc(price_ht, tax_rate_percent):
    """Return TTC from HT and tax rate percent using banking rounding (2 decimals).

    price_ht: number or Decimal
    tax_rate_percent: number (e.g., 20 for 20%) or None
    """
    if price_ht is None:
        return Decimal("0.00")

    try:
        price = Decimal(str(price_ht))
    except Exception:
        return Decimal("0.00")

    if tax_rate_percent in (None, "", False):
        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    try:
        rate = Decimal(str(tax_rate_percent))
    except Exception:
        rate = Decimal("0")

    factor = Decimal("1") + (rate / Decimal("100"))
    ttc_value = (price * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return ttc_value

@register.filter
def calculate_ttc(price_ht, tax_rate):
    """
    Calculate TTC price from HT price and tax rate percentage
    """
    if not price_ht or not tax_rate:
        return price_ht
    
    try:
        price_ht = float(price_ht)
        tax_rate = float(tax_rate)
        ttc_price = price_ht * (1 + tax_rate / 100)
        return round(ttc_price, 2)
    except (ValueError, TypeError):
        return price_ht

@register.filter
def calculate_tax_amount(price_ht, tax_rate):
    """
    Calculate tax amount from HT price and tax rate percentage
    """
    if not price_ht or not tax_rate:
        return 0
    
    try:
        price_ht = float(price_ht)
        tax_rate = float(tax_rate)
        tax_amount = price_ht * (tax_rate / 100)
        return round(tax_amount, 2)
    except (ValueError, TypeError):
        return 0

