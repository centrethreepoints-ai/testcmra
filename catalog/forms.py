from django import forms
from .models import PriceList, PriceListItem


class PriceListForm(forms.ModelForm):
    class Meta:
        model = PriceList
        fields = ['name', 'currency', 'is_active']


class PriceListItemForm(forms.ModelForm):
    class Meta:
        model = PriceListItem
        fields = ['product', 'fixed_price_ht', 'discount_percent']
        widgets = {
            'fixed_price_ht': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'discount_percent': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
        }


