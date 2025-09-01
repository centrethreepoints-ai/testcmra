"""
Views for reports application.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from decimal import Decimal
from datetime import datetime

from billing.models import Invoice


@login_required
def dashboard(request):
    company = request.user.company
    today = datetime.today()
    year = today.year
    month = today.month

    invoices = Invoice.objects.filter(company=company)

    # Totaux du mois
    sales_month = invoices.filter(invoice_type='sale', issue_date__year=year, issue_date__month=month).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0.00')
    purchases_month = invoices.filter(invoice_type='purchase', issue_date__year=year, issue_date__month=month).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0.00')

    # Soldes clients (AR) et fournisseurs (AP) depuis compta
    try:
        from accounting.models import Account, MoveLine
        receivable_accounts = Account.objects.filter(company=company, account_type='receivable')
        payable_accounts = Account.objects.filter(company=company, account_type='payable')
        ar_debit = MoveLine.objects.filter(account__in=receivable_accounts, move__posted=True).aggregate(Sum('debit'))['debit__sum'] or Decimal('0.00')
        ar_credit = MoveLine.objects.filter(account__in=receivable_accounts, move__posted=True).aggregate(Sum('credit'))['credit__sum'] or Decimal('0.00')
        ap_debit = MoveLine.objects.filter(account__in=payable_accounts, move__posted=True).aggregate(Sum('debit'))['debit__sum'] or Decimal('0.00')
        ap_credit = MoveLine.objects.filter(account__in=payable_accounts, move__posted=True).aggregate(Sum('credit'))['credit__sum'] or Decimal('0.00')
        ar_balance = ar_debit - ar_credit
        ap_balance = ap_credit - ap_debit
    except Exception:
        ar_balance = Decimal('0.00')
        ap_balance = Decimal('0.00')

    # Restant dû (somme des restants par facture)
    open_sales_qs = invoices.filter(invoice_type='sale').exclude(status='paid')
    open_purchases_qs = invoices.filter(invoice_type='purchase').exclude(status='paid')
    open_ar_total = sum((inv.get_remaining_amount() for inv in open_sales_qs), Decimal('0.00'))
    open_ap_total = sum((inv.get_remaining_amount() for inv in open_purchases_qs), Decimal('0.00'))

    # Récents
    recent_sales = invoices.filter(invoice_type='sale').order_by('-issue_date')[:5]
    recent_purchases = invoices.filter(invoice_type='purchase').order_by('-issue_date')[:5]

    context = {
        'sales_month': sales_month,
        'purchases_month': purchases_month,
        'ar_balance': ar_balance,
        'ap_balance': ap_balance,
        'open_ar_total': open_ar_total,
        'open_ap_total': open_ap_total,
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
        'year': year,
        'month': month,
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
def trial_balance(request):
    return render(request, 'reports/trial_balance.html', {})


@login_required
def general_ledger(request):
    return render(request, 'reports/general_ledger.html', {})


@login_required
def vat_return(request):
    return render(request, 'reports/vat_return.html', {})
