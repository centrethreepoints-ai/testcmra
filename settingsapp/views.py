"""
Views for settings application.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from companies.models import Company


@login_required
def company_settings(request):
    company: Company | None = getattr(request.user, 'company', None)
    if request.method == 'POST' and company:
        company.name = request.POST.get('name', company.name)
        company.email = request.POST.get('email', company.email)
        company.phone = request.POST.get('phone', company.phone)
        company.city = request.POST.get('city', company.city)
        logo = request.FILES.get('logo')
        update_fields = ['name', 'email', 'phone', 'city']
        if logo:
            company.logo = logo
            update_fields.append('logo')
        company.save(update_fields=update_fields)
        return redirect('settingsapp:company_settings')
    return render(request, 'settingsapp/company_settings.html', {'company': company})
