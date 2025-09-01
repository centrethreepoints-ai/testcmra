"""
Views for CRM application.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .models import Party, Contact
from billing.models import Quote, PurchaseOrder, Invoice, Payment


@login_required
def party_list(request):
    """Liste des parties (clients/fournisseurs)."""
    qs = Party.objects.filter(company=request.user.company).order_by('name')
    t = request.GET.get('type')  # 'customer', 'supplier', or ''
    q = request.GET.get('q', '')
    if t == 'customer':
        qs = qs.filter(is_customer=True)
    elif t == 'supplier':
        qs = qs.filter(is_supplier=True)
    if q:
        qs = qs.filter(name__icontains=q)
    counts = {
        'all': Party.objects.filter(company=request.user.company).count(),
        'customer': Party.objects.filter(company=request.user.company, is_customer=True).count(),
        'supplier': Party.objects.filter(company=request.user.company, is_supplier=True).count(),
    }
    return render(request, 'crm/party_list.html', {'parties': qs, 'filter_type': t or '', 'q': q, 'counts': counts})


@login_required
def party_detail(request, pk):
    """Détail d'une partie."""
    party = Party.objects.get(pk=pk, company=request.user.company)
    # Données liées
    quotes = Quote.objects.filter(company=request.user.company, party=party).order_by('-issue_date', '-id')[:5]
    purchase_orders = PurchaseOrder.objects.filter(company=request.user.company, party=party).order_by('-issue_date', '-id')[:5]
    invoices = Invoice.objects.filter(company=request.user.company, party=party).order_by('-issue_date', '-id')[:5]
    payments = Payment.objects.filter(company=request.user.company, party=party).order_by('-date', '-id')[:5]
    contacts = party.get_contacts()
    primary_contact = party.get_primary_contact()
    balance = party.get_balance()
    overdue_amount = party.get_overdue_amount()

    context = {
        'party': party,
        'quotes': quotes,
        'purchase_orders': purchase_orders,
        'invoices': invoices,
        'payments': payments,
        'contacts': contacts,
        'primary_contact': primary_contact,
        'balance': balance,
        'overdue_amount': overdue_amount,
    }
    return render(request, 'crm/party_detail.html', context)


@login_required
def contact_list(request):
    """Liste des contacts."""
    contacts = Contact.objects.filter(party__company=request.user.company).order_by('first_name')
    return render(request, 'crm/contact_list.html', {'contacts': contacts})


@login_required
def contact_detail(request, pk):
    """Détail d'un contact."""
    contact = Contact.objects.get(pk=pk, party__company=request.user.company)
    return render(request, 'crm/contact_detail.html', {'contact': contact})


class PartyListView(LoginRequiredMixin, ListView):
    """Vue liste des parties."""
    model = Party
    template_name = 'crm/party_list.html'
    context_object_name = 'parties'
    
    def get_queryset(self):
        qs = Party.objects.filter(company=self.request.user.company).order_by('name')
        t = self.request.GET.get('type')
        q = self.request.GET.get('q', '')
        if t == 'customer':
            qs = qs.filter(is_customer=True)
        elif t == 'supplier':
            qs = qs.filter(is_supplier=True)
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class PartyDetailView(LoginRequiredMixin, DetailView):
    """Vue détail d'une partie."""
    model = Party
    template_name = 'crm/party_detail.html'
    context_object_name = 'party'
    
    def get_queryset(self):
        return Party.objects.filter(company=self.request.user.company)


class PartyCreateView(LoginRequiredMixin, CreateView):
    """Vue création d'une partie."""
    model = Party
    template_name = 'crm/party_form.html'
    fields = [
        'name', 'ice', 'if_field', 'rc',
        'email', 'phone', 'mobile',
        'billing_address', 'shipping_address', 'city', 'postal_code', 'country',
        'payment_terms', 'credit_limit',
        'is_customer', 'is_supplier',
        'notes', 'tags'
    ]
    success_url = reverse_lazy('crm:party_list')
    
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)


class PartyUpdateView(LoginRequiredMixin, UpdateView):
    """Vue modification d'une partie."""
    model = Party
    template_name = 'crm/party_form.html'
    fields = [
        'name', 'ice', 'if_field', 'rc',
        'email', 'phone', 'mobile',
        'billing_address', 'shipping_address', 'city', 'postal_code', 'country',
        'payment_terms', 'credit_limit',
        'is_customer', 'is_supplier',
        'notes', 'tags'
    ]
    success_url = reverse_lazy('crm:party_list')
    
    def get_queryset(self):
        return Party.objects.filter(company=self.request.user.company)


class PartyDeleteView(LoginRequiredMixin, DeleteView):
    """Vue suppression d'une partie."""
    model = Party
    template_name = 'crm/party_confirm_delete.html'
    success_url = reverse_lazy('crm:party_list')
    
    def get_queryset(self):
        return Party.objects.filter(company=self.request.user.company)


class ContactListView(LoginRequiredMixin, ListView):
    """Vue liste des contacts."""
    model = Contact
    template_name = 'crm/contact_list.html'
    context_object_name = 'contacts'
    
    def get_queryset(self):
        return Contact.objects.filter(party__company=self.request.user.company).order_by('first_name')


class ContactDetailView(LoginRequiredMixin, DetailView):
    """Vue détail d'un contact."""
    model = Contact
    template_name = 'crm/contact_detail.html'
    context_object_name = 'contact'
    
    def get_queryset(self):
        return Contact.objects.filter(party__company=self.request.user.company)


class ContactCreateView(LoginRequiredMixin, CreateView):
    """Vue création d'un contact."""
    model = Contact
    template_name = 'crm/contact_form.html'
    fields = ['first_name', 'last_name', 'title', 'email', 'phone', 'mobile', 'is_primary', 'party', 'notes']
    success_url = reverse_lazy('crm:contact_list')
    
    def get_queryset(self):
        return Contact.objects.filter(party__company=self.request.user.company)


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    """Vue modification d'un contact."""
    model = Contact
    template_name = 'crm/contact_form.html'
    fields = ['first_name', 'last_name', 'title', 'email', 'phone', 'mobile', 'is_primary', 'party', 'notes']
    success_url = reverse_lazy('crm:contact_list')
    
    def get_queryset(self):
        return Contact.objects.filter(party__company=self.request.user.company)


class ContactDeleteView(LoginRequiredMixin, DeleteView):
    """Vue suppression d'un contact."""
    model = Contact
    template_name = 'crm/contact_confirm_delete.html'
    success_url = reverse_lazy('crm:contact_list')
    
    def get_queryset(self):
        return Contact.objects.filter(party__company=self.request.user.company)
