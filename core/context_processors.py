"""
Context processors for core application.
"""

from companies.models import Company


def company_context(request):
    """Ajouter les informations de la société au contexte global."""
    context = {}
    
    if request.user.is_authenticated:
        # Société liée par défaut
        default_company = getattr(request.user, 'company', None)
        context['company'] = default_company
        
        # Déterminer la société active (session > défaut > première M2M)
        active_company = None
        active_company_id = request.session.get('active_company_id')
        if active_company_id:
            try:
                if default_company and default_company.id == active_company_id:
                    active_company = default_company
                elif request.user.companies.filter(id=active_company_id).exists():
                    active_company = Company.objects.filter(id=active_company_id).first()
            except Exception:
                active_company = None
        if not active_company:
            active_company = default_company or request.user.companies.first()
        context['current_company'] = active_company
        
        # Informations supplémentaires
        if active_company:
            context['company_name'] = active_company.name
            context['company_logo'] = active_company.logo
            context['company_currency'] = active_company.default_currency
            context['fiscal_year'] = active_company.current_fiscal_year
    
    return context
