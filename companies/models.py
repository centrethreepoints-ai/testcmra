"""
Models for companies application.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import json


class Company(models.Model):
    """Modèle pour représenter une société."""
    
    CURRENCY_CHOICES = [
        ('MAD', 'Dirham Marocain (MAD)'),
        ('EUR', 'Euro (EUR)'),
        ('USD', 'Dollar US (USD)'),
    ]
    
    # Informations de base
    name = models.CharField(
        _('Nom de la société'),
        max_length=200,
        unique=True
    )
    
    # Informations légales Maroc
    ice = models.CharField(
        _('ICE'),
        max_length=15,
        blank=True,
        help_text=_('Identifiant Commerce Entreprise')
    )
    
    if_field = models.CharField(
        _('IF'),
        max_length=15,
        blank=True,
        help_text=_('Identifiant Fiscal')
    )
    
    rc = models.CharField(
        _('RC'),
        max_length=20,
        blank=True,
        help_text=_('Registre du Commerce')
    )
    
    cnss = models.CharField(
        _('CNSS'),
        max_length=20,
        blank=True,
        help_text=_('Numéro CNSS')
    )
    
    # Adresse
    address = models.TextField(
        _('Adresse'),
        blank=True
    )
    
    city = models.CharField(
        _('Ville'),
        max_length=100,
        blank=True
    )
    
    postal_code = models.CharField(
        _('Code postal'),
        max_length=10,
        blank=True
    )
    
    country = models.CharField(
        _('Pays'),
        max_length=100,
        default='Maroc'
    )
    
    # Contact
    phone = models.CharField(
        _('Téléphone'),
        max_length=20,
        blank=True
    )
    
    email = models.EmailField(
        _('Email'),
        blank=True
    )
    
    website = models.URLField(
        _('Site web'),
        blank=True
    )
    
    # Configuration
    logo = models.ImageField(
        _('Logo'),
        upload_to='company_logos/',
        blank=True,
        null=True
    )
    
    default_currency = models.CharField(
        _('Devise par défaut'),
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='MAD'
    )
    
    current_fiscal_year = models.CharField(
        _('Exercice fiscal en cours'),
        max_length=9,
        default='2024-2025',
        help_text=_('Format: YYYY-YYYY')
    )
    
    # Préférences (stockées en JSON)
    preferences = models.JSONField(
        _('Préférences'),
        default=dict,
        blank=True
    )

    # Helper defaults for feature flags
    def features_defaults(self) -> dict:
        return {
            'feature_emails_enabled': True,
            'feature_approvals_enabled': True,
            'feature_po_reception_enabled': True,
            'feature_stock_avg_cost_enabled': True,
            'feature_payments_advanced_enabled': True,
        }
    
    # TVA par défaut
    default_tax_rate = models.ForeignKey(
        'catalog.TaxRate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Taux de TVA par défaut'),
        related_name='default_for_companies'
    )
    
    # Statut
    is_active = models.BooleanField(
        _('Active'),
        default=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Société')
        verbose_name_plural = _('Sociétés')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validation personnalisée."""
        super().clean()
        
        # Validation de l'exercice fiscal
        if self.current_fiscal_year:
            try:
                year1, year2 = self.current_fiscal_year.split('-')
                if not (year1.isdigit() and year2.isdigit()):
                    raise ValueError
                if int(year2) != int(year1) + 1:
                    raise ValueError
            except ValueError:
                raise ValidationError({
                    'current_fiscal_year': _('Format invalide. Utilisez YYYY-YYYY (ex: 2024-2025)')
                })
    
    def get_preference(self, key, default=None):
        """Récupérer une préférence."""
        if key in self.preferences:
            return self.preferences.get(key)
        # fallback to feature defaults
        return self.features_defaults().get(key, default)
    
    def set_preference(self, key, value):
        """Définir une préférence."""
        self.preferences[key] = value
        self.save(update_fields=['preferences'])
    
    def get_sequence(self, code):
        """Récupérer une séquence par son code."""
        return self.sequences.filter(code=code).first()
    
    def get_next_number(self, sequence_code):
        """Obtenir le prochain numéro pour une séquence."""
        sequence = self.get_sequence(sequence_code)
        if sequence:
            return sequence.get_next_number()
        return None


class Sequence(models.Model):
    """Modèle pour gérer les séquences de numérotation des documents."""
    
    SEQUENCE_TYPES = [
        ('FAC', _('Facture')),
        ('DEV', _('Devis')),
        ('BC', _('Bon de commande')),
        ('AVOIR', _('Avoir')),
        ('RECU', _('Reçu')),
        ('BON', _('Bon de livraison')),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name=_('Société'),
        related_name='sequences'
    )
    
    code = models.CharField(
        _('Code'),
        max_length=10,
        choices=SEQUENCE_TYPES
    )
    
    name = models.CharField(
        _('Nom'),
        max_length=100
    )
    
    pattern = models.CharField(
        _('Modèle'),
        max_length=50,
        default='{code}-{year}-{seq:04d}',
        help_text=_('Variables disponibles: {code}, {year}, {seq}, {month}')
    )
    
    next_number = models.PositiveIntegerField(
        _('Prochain numéro'),
        default=1
    )
    
    prefix = models.CharField(
        _('Préfixe'),
        max_length=10,
        blank=True
    )
    
    suffix = models.CharField(
        _('Suffixe'),
        max_length=10,
        blank=True
    )
    
    reset_yearly = models.BooleanField(
        _('Remise à zéro annuelle'),
        default=True
    )
    
    is_active = models.BooleanField(
        _('Active'),
        default=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Séquence')
        verbose_name_plural = _('Séquences')
        unique_together = ['company', 'code']
        ordering = ['company', 'code']
    
    def __str__(self):
        return f"{self.company.name} - {self.get_code_display()}"
    
    def get_next_number(self):
        """Obtenir le prochain numéro et l'incrémenter."""
        current_number = self.next_number
        self.next_number += 1
        self.save(update_fields=['next_number'])
        return current_number
    
    def generate_number(self, **kwargs):
        """Générer un numéro selon le modèle."""
        from datetime import datetime
        
        context = {
            'code': self.code,
            'year': datetime.now().year,
            'month': datetime.now().month,
            'seq': self.get_next_number(),
        }
        context.update(kwargs)
        
        return self.pattern.format(**context)
    
    def reset_sequence(self):
        """Remettre la séquence à 1."""
        self.next_number = 1
        self.save(update_fields=['next_number'])
    
    def get_current_number(self):
        """Obtenir le numéro actuel sans l'incrémenter."""
        return self.next_number - 1
