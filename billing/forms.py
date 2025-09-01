from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import Quote, PurchaseOrder, Invoice, CreditNote, DocumentLine, Payment
from catalog.models import Product, TaxRate


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['party', 'discount_percent', 'withholding_tax_percent', 'notes', 'terms', 'validity_days']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['party', 'discount_percent', 'withholding_tax_percent', 'notes', 'terms', 'order_type', 'delivery_address', 'delivery_date']
        widgets = {
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['party', 'discount_percent', 'withholding_tax_percent', 'notes', 'terms', 'payment_terms', 'invoice_type']


class CreditNoteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None and getattr(user, 'company', None) is not None:
            self.fields['original_invoice'].queryset = Invoice.objects.filter(company=user.company).order_by('-issue_date', '-id')
        else:
            self.fields['original_invoice'].queryset = Invoice.objects.none()

    class Meta:
        model = CreditNote
        fields = [
            'original_invoice',
            'party',
            'credit_type',
            'discount_percent',
            'withholding_tax_percent',
            'notes',
            'terms',
            'reason',
        ]

class DocumentLineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Filter choices by current company if user provided
        if user is not None and getattr(user, 'company', None) is not None:
            self.fields['product'].queryset = Product.objects.filter(company=user.company).order_by('name')
            self.fields['tax_rate'].queryset = TaxRate.objects.filter(company=user.company, is_active=True).order_by('rate')
        else:
            self.fields['product'].queryset = Product.objects.none()
            self.fields['tax_rate'].queryset = TaxRate.objects.none()
    class Meta:
        model = DocumentLine
        fields = ['product', 'description', 'quantity', 'unit_price_ht', 'discount_percent', 'tax_rate']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Description'}),
            'quantity': forms.NumberInput(attrs={'step': '1', 'min': '1'}),
            'unit_price_ht': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'discount_percent': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
        }


class PaymentQuickForm(forms.Form):
    amount = forms.DecimalField(max_digits=12, decimal_places=2)
    method = forms.ChoiceField(choices=Payment.PAYMENT_METHODS)
    reference = forms.CharField(required=False)
