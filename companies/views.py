from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from .models import Company


@login_required
def switch_company(request, company_id: int):
    """Switch the active company for the current session, if the user has access."""
    user = request.user
    # Allow if this is the user's default company or in M2M membership
    allowed = False
    if user.company_id == company_id:
        allowed = True
    elif user.companies.filter(id=company_id).exists():
        allowed = True
    if not allowed:
        messages.error(request, "Accès refusé à cette société.")
        return redirect('core:dashboard')
    # Validate company exists and is active
    if not Company.objects.filter(id=company_id, is_active=True).exists():
        messages.error(request, "Société introuvable ou inactive.")
        return redirect('core:dashboard')
    request.session['active_company_id'] = company_id
    messages.success(request, "Société active mise à jour.")
    return redirect('core:dashboard')


@login_required
def company_list(request):
    """Liste des sociétés (admin seulement)."""
    if getattr(request.user, 'role', '') != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    companies = Company.objects.all().order_by('name')
    return render(request, 'companies/company_list.html', {'companies': companies})


@login_required
def company_create(request):
    """Création d'une société (admin seulement)."""
    if getattr(request.user, 'role', '') != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        city = request.POST.get('city', '').strip()
        default_currency = request.POST.get('default_currency', 'MAD')
        is_active = request.POST.get('is_active') == 'on'
        if not name:
            messages.error(request, 'Le nom de la société est requis.')
        else:
            company = Company.objects.create(
                name=name,
                email=email,
                phone=phone,
                city=city,
                default_currency=default_currency,
                is_active=is_active,
            )
            # Feature toggles
            try:
                flags = {
                    'feature_emails_enabled': request.POST.get('feature_emails_enabled') == 'on',
                    'feature_approvals_enabled': request.POST.get('feature_approvals_enabled') == 'on',
                    'feature_po_reception_enabled': request.POST.get('feature_po_reception_enabled') == 'on',
                    'feature_stock_avg_cost_enabled': request.POST.get('feature_stock_avg_cost_enabled') == 'on',
                    'feature_payments_advanced_enabled': request.POST.get('feature_payments_advanced_enabled') == 'on',
                }
                for k, v in flags.items():
                    company.set_preference(k, v)
            except Exception:
                pass
            # Donner accès à l'admin courant
            try:
                request.user.companies.add(company)
            except Exception:
                pass
            messages.success(request, 'Société créée avec succès.')
            return redirect('companies:company_list')
    # Defaults for feature flags on create
    flags = {
        'feature_emails_enabled': True,
        'feature_approvals_enabled': True,
        'feature_po_reception_enabled': True,
        'feature_stock_avg_cost_enabled': True,
        'feature_payments_advanced_enabled': True,
    }
    return render(request, 'companies/company_form.html', {'mode': 'create', 'flags': flags})


@login_required
def company_edit(request, pk: int):
    """Édition d'une société (admin seulement)."""
    if getattr(request.user, 'role', '') != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        city = request.POST.get('city', '').strip()
        default_currency = request.POST.get('default_currency', company.default_currency)
        is_active = request.POST.get('is_active') == 'on'
        if not name:
            messages.error(request, 'Le nom de la société est requis.')
        else:
            company.name = name
            company.email = email
            company.phone = phone
            company.city = city
            company.default_currency = default_currency
            company.is_active = is_active
            company.save()
            # Update feature toggles
            try:
                flags = {
                    'feature_emails_enabled': request.POST.get('feature_emails_enabled') == 'on',
                    'feature_approvals_enabled': request.POST.get('feature_approvals_enabled') == 'on',
                    'feature_po_reception_enabled': request.POST.get('feature_po_reception_enabled') == 'on',
                    'feature_stock_avg_cost_enabled': request.POST.get('feature_stock_avg_cost_enabled') == 'on',
                    'feature_payments_advanced_enabled': request.POST.get('feature_payments_advanced_enabled') == 'on',
                }
                for k, v in flags.items():
                    company.set_preference(k, v)
            except Exception:
                pass
            messages.success(request, 'Société mise à jour avec succès.')
            return redirect('companies:company_list')
    flags = {
        'feature_emails_enabled': company.get_preference('feature_emails_enabled', True),
        'feature_approvals_enabled': company.get_preference('feature_approvals_enabled', True),
        'feature_po_reception_enabled': company.get_preference('feature_po_reception_enabled', True),
        'feature_stock_avg_cost_enabled': company.get_preference('feature_stock_avg_cost_enabled', True),
        'feature_payments_advanced_enabled': company.get_preference('feature_payments_advanced_enabled', True),
    }
    return render(request, 'companies/company_form.html', {'mode': 'edit', 'company': company, 'flags': flags})


