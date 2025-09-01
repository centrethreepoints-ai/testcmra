"""
Views for accounting application.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from django.db.models import Sum

from .models import Move, Journal, Account, VatPeriod


@login_required
@role_required('comptable')
def move_list(request):
    moves = Move.objects.filter(company=request.user.company).order_by('-date')[:50]
    return render(request, 'accounting/move_list.html', {'moves': moves})


@login_required
@role_required('comptable')
def move_detail(request, pk):
    move = get_object_or_404(Move, pk=pk, company=request.user.company)
    return render(request, 'accounting/move_detail.html', {'move': move})


@login_required
@role_required('comptable')
def journal_list(request):
    journals = Journal.objects.filter(company=request.user.company).order_by('code')
    return render(request, 'accounting/journal_list.html', {'journals': journals})


@login_required
@role_required('comptable')
def account_list(request):
    accounts = Account.objects.filter(company=request.user.company).order_by('code')
    return render(request, 'accounting/account_list.html', {'accounts': accounts})


@login_required
@role_required('comptable')
def trial_balance(request):
    accounts = Account.objects.filter(company=request.user.company).order_by('code')
    rows = []
    for acc in accounts:
        debit = acc.move_lines.filter(move__posted=True).aggregate(s=Sum('debit'))['s'] or 0
        credit = acc.move_lines.filter(move__posted=True).aggregate(s=Sum('credit'))['s'] or 0
        rows.append({'account': acc, 'debit': debit, 'credit': credit, 'balance': debit - credit})
    return render(request, 'accounting/reports/trial_balance.html', {'rows': rows})


@login_required
@role_required('comptable')
def general_ledger(request):
    accounts = Account.objects.filter(company=request.user.company).order_by('code')
    return render(request, 'accounting/reports/general_ledger.html', {'accounts': accounts})


@login_required
@role_required('comptable')
def vat_return(request):
    period = VatPeriod.objects.filter(company=request.user.company).order_by('-period_start').first()
    if period:
        period.calculate_vat_totals()
    return render(request, 'accounting/reports/vat_return.html', {'period': period})


@login_required
@role_required('comptable')
def ar_ap_dashboard(request):
    rec_accounts = Account.objects.filter(company=request.user.company, account_type='receivable')
    pay_accounts = Account.objects.filter(company=request.user.company, account_type='payable')
    from django.db.models import Sum
    rec_debit = rec_accounts.values('id')
    from accounting.models import MoveLine
    rd = MoveLine.objects.filter(account__in=rec_accounts, move__posted=True).aggregate(Sum('debit'))['debit__sum'] or 0
    rc = MoveLine.objects.filter(account__in=rec_accounts, move__posted=True).aggregate(Sum('credit'))['credit__sum'] or 0
    pd = MoveLine.objects.filter(account__in=pay_accounts, move__posted=True).aggregate(Sum('debit'))['debit__sum'] or 0
    pc = MoveLine.objects.filter(account__in=pay_accounts, move__posted=True).aggregate(Sum('credit'))['credit__sum'] or 0
    ar_balance = (rd - rc)
    ap_balance = (pc - pd)
    return render(request, 'accounting/reports/ar_ap.html', {'ar_balance': ar_balance, 'ap_balance': ap_balance})
