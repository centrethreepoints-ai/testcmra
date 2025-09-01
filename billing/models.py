"""
Models for billing application.
"""

from django.db import models
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP
import uuid


def quantize_money(value: Decimal) -> Decimal:
    if value is None:
        return Decimal('0.00')
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class AbstractDocument(models.Model):
    """Modèle abstrait pour tous les documents de facturation."""
    
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('sent', _('Envoyé')),
        ('approved', _('Approuvé')),
        ('validated', _('Validé')),
        ('paid', _('Payé')),
        ('partial', _('Partiellement payé')),
        ('cancelled', _('Annulé')),
    ]
    
    # Informations de base
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        verbose_name=_('Société'),
        related_name='%(class)s_documents'
    )
    
    party = models.ForeignKey(
        'crm.Party',
        on_delete=models.CASCADE,
        verbose_name=_('Partie'),
        related_name='%(class)s_documents'
    )
    
    # Numérotation
    sequence_code = models.CharField(
        _('Code séquence'),
        max_length=10,
        blank=True
    )
    
    number = models.CharField(
        _('Numéro'),
        max_length=50,
        unique=True
    )
    
    # Dates
    issue_date = models.DateField(
        _('Date d\'émission'),
        auto_now_add=True
    )
    
    due_date = models.DateField(
        _('Date d\'échéance'),
        null=True,
        blank=True
    )
    
    # Statut et montants
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    currency = models.CharField(
        _('Devise'),
        max_length=3,
        default='MAD'
    )
    
    exchange_rate = models.DecimalField(
        _('Taux de change'),
        max_digits=10,
        decimal_places=6,
        default=Decimal('1.000000')
    )
    
    # Totaux
    total_ht = models.DecimalField(
        _('Total HT'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total_tva = models.DecimalField(
        _('Total TVA'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total_ttc = models.DecimalField(
        _('Total TTC'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Remises et retenues
    discount_percent = models.DecimalField(
        _('Remise (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    discount_amount = models.DecimalField(
        _('Remise (montant)'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    withholding_tax_percent = models.DecimalField(
        _('Retenue à la source (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    withholding_tax_amount = models.DecimalField(
        _('Retenue à la source (montant)'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Notes et conditions
    notes = models.TextField(
        _('Notes'),
        blank=True
    )
    
    terms = models.TextField(
        _('Conditions'),
        blank=True
    )
    
    # Lignes (relation générique inverse)
    lines = GenericRelation(
        'billing.DocumentLine',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='document'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-issue_date', '-created_at']
    
    def __str__(self):
        return f"{self.number} - {self.party.name}"
    
    def calculate_totals(self):
        """Calculer tous les totaux avec arrondi commercial 2 décimales."""
        lines = self.lines.all()
        
        # Total HT des lignes
        total_ht = lines.aggregate(total=Sum('total_line_ht'))['total'] or Decimal('0.00')
        total_ht = quantize_money(total_ht)
        
        # Remise
        if self.discount_percent > 0:
            discount_amount = quantize_money(total_ht * (self.discount_percent / Decimal('100.00')))
            self.discount_amount = discount_amount
            total_ht_after_discount = quantize_money(total_ht - discount_amount)
        else:
            total_ht_after_discount = total_ht
        
        # Total TVA
        total_tva = lines.aggregate(total=Sum('total_line_tva'))['total'] or Decimal('0.00')
        total_tva = quantize_money(total_tva)
        
        # Total TTC
        total_ttc = quantize_money(total_ht_after_discount + total_tva)
        
        # Retenue à la source
        if self.withholding_tax_percent > 0:
            withholding_amount = quantize_money(total_ht_after_discount * (self.withholding_tax_percent / Decimal('100.00')))
            self.withholding_tax_amount = withholding_amount
            total_ttc = quantize_money(total_ttc - withholding_amount)
        
        # Mettre à jour les totaux
        self.total_ht = total_ht
        self.total_tva = total_tva
        self.total_ttc = total_ttc
        
        return {
            'total_ht': self.total_ht,
            'total_tva': self.total_tva,
            'total_ttc': self.total_ttc,
            'discount_amount': self.discount_amount,
            'withholding_tax_amount': self.withholding_tax_amount
        }
    
    def can_be_validated(self):
        """Vérifier si le document peut être validé."""
        return self.status == 'draft' and self.lines.exists()
    
    def can_be_cancelled(self):
        """Vérifier si le document peut être annulé."""
        return self.status in ['draft', 'sent', 'approved']
    
    def get_paid_amount(self):
        """Obtenir le montant payé."""
        from .models import PaymentAllocation
        
        allocations = PaymentAllocation.objects.filter(
            content_type=ContentType.objects.get_for_model(self),
            document_id=self.id
        )
        
        return allocations.aggregate(total=Sum('allocated_amount'))['total'] or Decimal('0.00')
    
    def get_remaining_amount(self):
        """Obtenir le montant restant à payer."""
        return self.total_ttc - self.get_paid_amount()


class Quote(AbstractDocument):
    """Modèle pour les devis."""
    
    VALIDITY_CHOICES = [
        (15, _('15 jours')),
        (30, _('30 jours')),
        (60, _('60 jours')),
        (90, _('90 jours')),
    ]
    
    validity_days = models.PositiveIntegerField(
        _('Validité (jours)'),
        choices=VALIDITY_CHOICES,
        default=30
    )
    
    valid_until = models.DateField(
        _('Valide jusqu\'au'),
        null=True,
        blank=True
    )
    
    is_converted = models.BooleanField(
        _('Converti'),
        default=False
    )
    
    converted_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Converti en'),
        related_name='converted_from'
    )
    
    # Nouveaux champs de suivi
    converted_po = models.ForeignKey(
        'billing.PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='origin_quotes',
        verbose_name=_('Bon de commande généré')
    )
    converted_at = models.DateTimeField(
        _('Converti le'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Devis')
        verbose_name_plural = _('Devis')
    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        """Calculer la date de validité."""
        if self.issue_date and self.validity_days:
            from datetime import timedelta
            self.valid_until = self.issue_date + timedelta(days=self.validity_days)
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Vérifier si le devis est expiré."""
        if not self.valid_until:
            return False
        
        from django.utils import timezone
        return timezone.now().date() > self.valid_until
    
    def convert_to_invoice(self):
        """Convertir le devis en facture."""
        from .models import Invoice
        
        if self.is_converted:
            return None
        
        # Créer la facture
        invoice = Invoice.objects.create(
            company=self.company,
            party=self.party,
            issue_date=self.issue_date,
            due_date=self.due_date,
            currency=self.currency,
            exchange_rate=self.exchange_rate,
            discount_percent=self.discount_percent,
            withholding_tax_percent=self.withholding_tax_percent,
            notes=self.notes,
            terms=self.terms
        )
        
        # Copier les lignes
        for line in self.lines.all():
            line.pk = None
            line.document = invoice
            line.save()
        
        # Marquer comme converti
        self.is_converted = True
        self.converted_to = invoice
        self.save()
        
        return invoice


class PurchaseOrder(AbstractDocument):
    """Modèle pour les bons de commande."""
    
    ORDER_TYPES = [
        ('purchase', _('Achat')),
        ('sale', _('Vente')),
    ]
    
    order_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=ORDER_TYPES,
        default='purchase'
    )
    
    delivery_address = models.TextField(
        _('Adresse de livraison'),
        blank=True
    )
    
    delivery_date = models.DateField(
        _('Date de livraison souhaitée'),
        null=True,
        blank=True
    )
    
    # Suivi de conversion vers facture
    converted_invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='from_purchase_order',
        verbose_name=_('Facture générée')
    )
    converted_at = models.DateTimeField(
        _('Converti le'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Bon de commande')
        verbose_name_plural = _('Bons de commande')
    history = HistoricalRecords()


class Invoice(AbstractDocument):
    """Modèle pour les factures."""
    
    INVOICE_TYPES = [
        ('sale', _('Vente')),
        ('purchase', _('Achat')),
    ]
    
    invoice_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=INVOICE_TYPES,
        default='sale'
    )
    
    # Références
    quote = models.ForeignKey(
        Quote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Devis d\'origine'),
        related_name='invoices'
    )
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Bon de commande'),
        related_name='invoices'
    )
    
    # Paiement
    payment_terms = models.PositiveIntegerField(
        _('Conditions de paiement (jours)'),
        default=30
    )
    
    # Comptabilité
    is_posted = models.BooleanField(
        _('Comptabilisé'),
        default=False
    )
    
    posted_at = models.DateTimeField(
        _('Comptabilisé le'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Facture')
        verbose_name_plural = _('Factures')
    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        """Calculer la date d'échéance si pas définie."""
        if not self.due_date and self.issue_date:
            from datetime import timedelta
            self.due_date = self.issue_date + timedelta(days=self.payment_terms)
        
        super().save(*args, **kwargs)
    
    def post_to_accounting(self):
        """Comptabiliser la facture."""
        if self.is_posted:
            return False
        
        from accounting.services.posting import post_invoice
        
        try:
            post_invoice(self)
            self.is_posted = True
            self.posted_at = timezone.now()
            self.save(update_fields=['is_posted', 'posted_at'])
            return True
        except Exception as e:
            # Log l'erreur
            return False


class CreditNote(AbstractDocument):
    """Modèle pour les avoirs."""
    
    CREDIT_TYPES = [
        ('full', _('Annulation totale')),
        ('partial', _('Annulation partielle')),
        ('discount', _('Remise/Escompte')),
    ]
    
    credit_type = models.CharField(
        _('Type d\'avoir'),
        max_length=20,
        choices=CREDIT_TYPES,
        default='partial'
    )
    
    original_invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        verbose_name=_('Facture d\'origine'),
        related_name='credit_notes'
    )
    
    reason = models.TextField(
        _('Motif'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('Avoir')
        verbose_name_plural = _('Avoirs')
    history = HistoricalRecords()


class DocumentLine(models.Model):
    """Modèle pour les lignes de documents."""
    
    # Référence générique au document
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    document = GenericForeignKey('content_type', 'object_id')
    
    # Produit/Service
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.PROTECT,
        verbose_name=_('Produit/Service'),
        related_name='document_lines'
    )
    
    description = models.TextField(
        _('Description'),
        blank=True
    )
    
    quantity = models.PositiveIntegerField(
        _('Quantité'),
        validators=[MinValueValidator(1)],
        default=1
    )
    
    unit_price_ht = models.DecimalField(
        _('Prix unitaire HT'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    discount_percent = models.DecimalField(
        _('Remise (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    discount_amount = models.DecimalField(
        _('Remise (montant)'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    tax_rate = models.ForeignKey(
        'catalog.TaxRate',
        on_delete=models.PROTECT,
        verbose_name=_('Taux de TVA'),
        related_name='document_lines'
    )
    
    total_line_ht = models.DecimalField(
        _('Total ligne HT'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total_line_tva = models.DecimalField(
        _('Total ligne TVA'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total_line_ttc = models.DecimalField(
        _('Total ligne TTC'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Ligne de document')
        verbose_name_plural = _('Lignes de document')
        ordering = ['id']
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} x {self.unit_price_ht}"
    
    def calculate_totals(self):
        """Calculs avec arrondi bancaire (2 décimales, HALF_UP)."""
        base = quantize_money(self.unit_price_ht * Decimal(self.quantity))
        if self.discount_percent > 0:
            self.discount_amount = quantize_money(base * (self.discount_percent / Decimal('100.00')))
            total_ht = quantize_money(base - self.discount_amount)
        else:
            self.discount_amount = Decimal('0.00')
            total_ht = base
        total_tva = quantize_money(total_ht * self.tax_rate.get_rate_decimal())
        total_ttc = quantize_money(total_ht + total_tva)
        self.total_line_ht = total_ht
        self.total_line_tva = total_tva
        self.total_line_ttc = total_ttc
        return {
            'total_line_ht': self.total_line_ht,
            'total_line_tva': self.total_line_tva,
            'total_line_ttc': self.total_line_ttc
        }
    
    def save(self, *args, **kwargs):
        """Calculer les totaux avant la sauvegarde."""
        self.calculate_totals()
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Modèle pour les paiements."""
    
    PAYMENT_METHODS = [
        ('cash', _('Espèces')),
        ('transfer', _('Virement')),
        ('check', _('Chèque')),
        ('card', _('Carte bancaire')),
        ('other', _('Autre')),
    ]
    
    PAYMENT_TYPES = [
        ('receipt', _('Encaissement')),
        ('disbursement', _('Décaissement')),
    ]
    
    # Informations de base
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        verbose_name=_('Société'),
        related_name='payments'
    )
    
    party = models.ForeignKey(
        'crm.Party',
        on_delete=models.CASCADE,
        verbose_name=_('Partie'),
        related_name='payments'
    )
    
    # Paiement
    payment_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=PAYMENT_TYPES,
        default='receipt'
    )
    
    method = models.CharField(
        _('Moyen de paiement'),
        max_length=20,
        choices=PAYMENT_METHODS,
        default='transfer'
    )
    
    amount = models.DecimalField(
        _('Montant'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    currency = models.CharField(
        _('Devise'),
        max_length=3,
        default='MAD'
    )
    
    exchange_rate = models.DecimalField(
        _('Taux de change'),
        max_digits=10,
        decimal_places=6,
        default=Decimal('1.000000')
    )
    
    # Références
    reference = models.CharField(
        _('Référence'),
        max_length=100,
        blank=True
    )
    
    check_number = models.CharField(
        _('Numéro de chèque'),
        max_length=20,
        blank=True
    )
    
    bank_name = models.CharField(
        _('Nom de la banque'),
        max_length=100,
        blank=True
    )
    
    # Dates
    date = models.DateField(
        _('Date de paiement'),
        auto_now_add=True
    )
    
    value_date = models.DateField(
        _('Date de valeur'),
        null=True,
        blank=True
    )
    
    # Notes
    notes = models.TextField(
        _('Notes'),
        blank=True
    )
    
    # Statut
    is_reconciled = models.BooleanField(
        _('Rapproché'),
        default=False
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-date', '-created_at']
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.reference or self.id} - {self.party.name} - {self.amount}"
    
    def get_amount_in_company_currency(self):
        """Obtenir le montant dans la devise de la société."""
        return self.amount * self.exchange_rate
    
    def reconcile(self):
        """Marquer le paiement comme rapproché."""
        self.is_reconciled = True
        self.save(update_fields=['is_reconciled'])


class PaymentAllocation(models.Model):
    """Modèle pour l'allocation des paiements aux factures."""
    
    # Paiement
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        verbose_name=_('Paiement'),
        related_name='allocations'
    )
    
    # Document (facture, avoir, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    document_id = models.PositiveIntegerField()
    document = GenericForeignKey('content_type', 'document_id')
    
    # Montant alloué
    allocated_amount = models.DecimalField(
        _('Montant alloué'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Groupe de lettrage
    reconciliation_group = models.UUIDField(
        _('Groupe de lettrage'),
        default=uuid.uuid4,
        editable=False
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Allocation de paiement')
        verbose_name_plural = _('Allocations de paiement')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment.reference} -> {self.document} ({self.allocated_amount})"
    
    def clean(self):
        """Validation personnalisée."""
        super().clean()
        
        # Vérifier que le montant alloué ne dépasse pas le montant du paiement
        total_allocated = PaymentAllocation.objects.filter(
            payment=self.payment
        ).exclude(pk=self.pk).aggregate(
            total=Sum('allocated_amount')
        )['total'] or Decimal('0.00')
        
        if total_allocated + self.allocated_amount > self.payment.amount:
            raise ValidationError({
                'allocated_amount': _('Le montant alloué dépasse le montant disponible du paiement.')
            })


class PaymentSchedule(models.Model):
    """Échéancier de paiement pour les factures."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('paid', _('Payé')),
        ('overdue', _('En retard')),
        ('cancelled', _('Annulé')),
    ]
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        verbose_name=_('Facture'),
        related_name='payment_schedules'
    )
    
    due_date = models.DateField(_('Date d\'échéance'))
    amount = models.DecimalField(_('Montant'), max_digits=12, decimal_places=2)
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Paiement associé
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Paiement'),
        related_name='scheduled_payments'
    )
    
    # Notes
    notes = models.TextField(_('Notes'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Échéance de paiement')
        verbose_name_plural = _('Échéances de paiement')
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.invoice.number} - {self.due_date} - {self.amount}"
    
    def is_overdue(self):
        """Vérifier si l'échéance est en retard."""
        from django.utils import timezone
        return self.status == 'pending' and self.due_date < timezone.now().date()
    
    def mark_as_paid(self, payment):
        """Marquer l'échéance comme payée."""
        self.status = 'paid'
        self.payment = payment
        self.save(update_fields=['status', 'payment'])


class BankReconciliation(models.Model):
    """Rapprochement bancaire."""
    
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('reconciled', _('Rapproché')),
        ('closed', _('Clôturé')),
    ]
    
    bank_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.CASCADE,
        verbose_name=_('Compte bancaire'),
        related_name='reconciliations'
    )
    
    statement_date = models.DateField(_('Date de relevé'))
    statement_balance = models.DecimalField(_('Solde du relevé'), max_digits=12, decimal_places=2)
    book_balance = models.DecimalField(_('Solde comptable'), max_digits=12, decimal_places=2)
    difference = models.DecimalField(_('Différence'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='draft')
    reconciled = models.BooleanField(_('Rapproché'), default=False)
    
    # Notes
    notes = models.TextField(_('Notes'), blank=True)
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey('users.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Rapprochement bancaire')
        verbose_name_plural = _('Rapprochements bancaires')
        ordering = ['-statement_date']
    
    def __str__(self):
        return f"{self.bank_account.name} - {self.statement_date}"
    
    def calculate_difference(self):
        """Calculer la différence entre le relevé et la comptabilité."""
        self.difference = self.statement_balance - self.book_balance
        return self.difference
    
    def save(self, *args, **kwargs):
        """Calculer la différence avant la sauvegarde."""
        if not self.pk or 'statement_balance' in kwargs.get('update_fields', []):
            self.calculate_difference()
        super().save(*args, **kwargs)


class EmailTemplate(models.Model):
    """Modèle pour les modèles d'emails."""
    
    TEMPLATE_TYPES = [
        ('invoice', _('Facture')),
        ('quote', _('Devis')),
        ('reminder', _('Relance')),
        ('payment_confirmation', _('Confirmation de paiement')),
        ('overdue_notice', _('Avis d\'impayé')),
        ('general', _('Général')),
    ]
    
    name = models.CharField(_('Nom'), max_length=100)
    subject = models.CharField(_('Objet'), max_length=200)
    body = models.TextField(_('Corps du message'))
    template_type = models.CharField(_('Type'), max_length=50, choices=TEMPLATE_TYPES)
    
    # Variables disponibles dans le template
    available_variables = models.TextField(
        _('Variables disponibles'),
        blank=True,
        help_text=_('Liste des variables disponibles pour ce type de template')
    )
    
    # Statut
    active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey('users.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Modèle d\'email')
        verbose_name_plural = _('Modèles d\'emails')
        unique_together = ['name', 'company']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def get_rendered_subject(self, context):
        """Rendre le sujet avec le contexte."""
        from django.template import Template, Context
        template = Template(self.subject)
        return template.render(Context(context))
    
    def get_rendered_body(self, context):
        """Rendre le corps avec le contexte."""
        from django.template import Template, Context
        template = Template(self.body)
        return template.render(Context(context))


class EmailLog(models.Model):
    """Modèle pour tracer l'envoi des emails."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('sent', _('Envoyé')),
        ('failed', _('Échec')),
        ('cancelled', _('Annulé')),
    ]
    
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        verbose_name=_('Modèle'),
        related_name='email_logs'
    )
    
    recipient = models.EmailField(_('Destinataire'))
    subject = models.CharField(_('Objet'), max_length=200)
    body = models.TextField(_('Corps du message'))
    
    # Statut et suivi
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(_('Envoyé le'), null=True, blank=True)
    error_message = models.TextField(_('Message d\'erreur'), blank=True)
    
    # Contexte de l'envoi
    context_data = models.JSONField(_('Données de contexte'), default=dict, blank=True)
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey('users.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Log d\'email')
        verbose_name_plural = _('Logs d\'emails')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient} - {self.subject} ({self.get_status_display()})"
    
    def mark_as_sent(self):
        """Marquer l'email comme envoyé."""
        from django.utils import timezone
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_failed(self, error_message):
        """Marquer l'email comme échoué."""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
