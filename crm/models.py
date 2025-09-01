"""
Models for CRM application.
"""

from django.db import models
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.db.models import Sum
from decimal import Decimal


class Party(models.Model):
    """Modèle pour les clients et fournisseurs."""
    
    PARTY_TYPES = [
        ('customer', _('Client')),
        ('supplier', _('Fournisseur')),
        ('both', _('Client et Fournisseur')),
    ]
    
    # Informations de base
    name = models.CharField(
        _('Nom/Raison sociale'),
        max_length=200
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
    
    # Type de partie
    is_customer = models.BooleanField(
        _('Est un client'),
        default=False
    )
    
    is_supplier = models.BooleanField(
        _('Est un fournisseur'),
        default=False
    )
    
    party_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=PARTY_TYPES,
        default='customer'
    )
    
    # Contact principal
    email = models.EmailField(
        _('Email'),
        blank=True
    )
    
    phone = models.CharField(
        _('Téléphone'),
        max_length=20,
        blank=True
    )
    
    mobile = models.CharField(
        _('Mobile'),
        max_length=20,
        blank=True
    )
    
    # Adresses
    billing_address = models.TextField(
        _('Adresse de facturation'),
        blank=True
    )
    
    shipping_address = models.TextField(
        _('Adresse de livraison'),
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
    
    # Informations commerciales
    payment_terms = models.PositiveIntegerField(
        _('Conditions de paiement (jours)'),
        default=30,
        help_text=_('Nombre de jours pour le paiement')
    )
    
    credit_limit = models.DecimalField(
        _('Limite de crédit'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Limite de crédit autorisée')
    )
    
    # Comptabilité
    account_receivable = models.CharField(
        _('Compte client'),
        max_length=20,
        blank=True,
        help_text=_('Compte comptable client (ex: 411)')
    )
    
    account_payable = models.CharField(
        _('Compte fournisseur'),
        max_length=20,
        blank=True,
        help_text=_('Compte comptable fournisseur (ex: 401)')
    )
    
    # Notes et tags
    notes = models.TextField(
        _('Notes'),
        blank=True
    )
    
    tags = models.CharField(
        _('Tags'),
        max_length=200,
        blank=True,
        help_text=_('Tags séparés par des virgules')
    )
    # Liste de prix retirée
    
    # Société
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        verbose_name=_('Société'),
        related_name='parties'
    )
    
    # Statut
    is_active = models.BooleanField(
        _('Actif'),
        default=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Partie')
        verbose_name_plural = _('Parties')
        ordering = ['name']
        unique_together = ['company', 'name']
    
    def __str__(self):
        return self.name
    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        """Mettre à jour le type automatiquement."""
        if self.is_customer and self.is_supplier:
            self.party_type = 'both'
        elif self.is_supplier:
            self.party_type = 'supplier'
        elif self.is_customer:
            self.party_type = 'customer'
        
        super().save(*args, **kwargs)
    
    def get_balance(self):
        """Calculer le solde (positif = nous doit, négatif = nous devons)."""
        from billing.models import Invoice, Payment
        
        # Factures clients (nous devons recevoir)
        customer_invoices = Invoice.objects.filter(
            party=self,
            company=self.company,
            status__in=['validated', 'sent', 'partial']
        ).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0.00')
        
        # Paiements clients reçus
        customer_payments = Payment.objects.filter(
            party=self,
            company=self.company,
            amount__gt=0
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Factures fournisseurs (nous devons payer)
        supplier_invoices = Invoice.objects.filter(
            party=self,
            company=self.company,
            status__in=['validated', 'sent', 'partial']
        ).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0.00')
        
        # Paiements fournisseurs effectués
        supplier_payments = Payment.objects.filter(
            party=self,
            company=self.company,
            amount__lt=0
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Solde = (factures clients - paiements clients) - (factures fournisseurs - paiements fournisseurs)
        balance = (customer_invoices - customer_payments) - (supplier_invoices - supplier_payments)
        
        return balance
    
    def get_overdue_amount(self):
        """Calculer le montant en retard de paiement."""
        from billing.models import Invoice
        from django.utils import timezone
        
        overdue_invoices = Invoice.objects.filter(
            party=self,
            company=self.company,
            status__in=['validated', 'sent'],
            due_date__lt=timezone.now().date()
        )
        
        return overdue_invoices.aggregate(total=Sum('total_ttc'))['total'] or Decimal('0.00')
    
    def get_contacts(self):
        """Obtenir tous les contacts de cette partie."""
        return self.contacts.filter(is_active=True)
    
    def get_primary_contact(self):
        """Obtenir le contact principal."""
        return self.contacts.filter(is_primary=True, is_active=True).first()


class Contact(models.Model):
    """Modèle pour les contacts des parties."""
    
    # Informations de base
    first_name = models.CharField(
        _('Prénom'),
        max_length=100
    )
    
    last_name = models.CharField(
        _('Nom'),
        max_length=100
    )
    
    title = models.CharField(
        _('Fonction'),
        max_length=100,
        blank=True
    )
    
    # Contact
    email = models.EmailField(
        _('Email'),
        blank=True
    )
    
    phone = models.CharField(
        _('Téléphone'),
        max_length=20,
        blank=True
    )
    
    mobile = models.CharField(
        _('Mobile'),
        max_length=20,
        blank=True
    )
    
    # Relations
    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        verbose_name=_('Partie'),
        related_name='contacts'
    )
    
    is_primary = models.BooleanField(
        _('Contact principal'),
        default=False
    )
    
    # Notes
    notes = models.TextField(
        _('Notes'),
        blank=True
    )
    
    # Statut
    is_active = models.BooleanField(
        _('Actif'),
        default=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    history = HistoricalRecords()
    
    def get_full_name(self):
        """Obtenir le nom complet."""
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        """S'assurer qu'il n'y a qu'un seul contact principal par partie."""
        if self.is_primary:
            # Désactiver les autres contacts principaux de la même partie
            Contact.objects.filter(
                party=self.party,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)
