"""
Models for accounting application.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from decimal import Decimal
import uuid


class Journal(models.Model):
    """Modèle pour les journaux comptables."""
    
    JOURNAL_TYPES = [
        ('VEN', _('Ventes')),
        ('ACH', _('Achats')),
        ('BQ', _('Banque')),
        ('CAI', _('Caisse')),
        ('MIS', _('Divers')),
        ('OD', _('Opérations diverses')),
    ]
    
    # Informations de base
    code = models.CharField(
        _('Code'),
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9]{2,10}$',
                message=_('Le code doit contenir 2 à 10 caractères majuscules et chiffres.')
            )
        ]
    )
    
    name = models.CharField(
        _('Nom'),
        max_length=100
    )
    
    journal_type = models.CharField(
        _('Type'),
        max_length=10,
        choices=JOURNAL_TYPES,
        default='MIS'
    )
    
    # Configuration
    is_active = models.BooleanField(
        _('Actif'),
        default=True
    )
    
    allow_negative_balance = models.BooleanField(
        _('Autoriser solde négatif'),
        default=False
    )
    
    # Société
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        verbose_name=_('Société'),
        related_name='journals'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Journal')
        verbose_name_plural = _('Journaux')
        ordering = ['code']
        unique_together = ['company', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_balance(self, date=None):
        """Obtenir le solde du journal à une date donnée."""
        moves = self.moves.filter(posted=True)
        
        if date:
            moves = moves.filter(date__lte=date)
        
        total_debit = moves.aggregate(total=Sum('total_debit'))['total'] or Decimal('0.00')
        total_credit = moves.aggregate(total=Sum('total_credit'))['total'] or Decimal('0.00')
        
        return total_debit - total_credit


class Account(models.Model):
    """Modèle pour le plan comptable."""
    
    ACCOUNT_TYPES = [
        ('asset', _('Actif')),
        ('liability', _('Passif')),
        ('equity', _('Capitaux propres')),
        ('income', _('Produits')),
        ('expense', _('Charges')),
        ('tax', _('Taxes')),
        ('receivable', _('Créances')),
        ('payable', _('Dettes')),
        ('cash', _('Trésorerie')),
        ('bank', _('Banque')),
    ]
    
    # Informations de base
    code = models.CharField(
        _('Code'),
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{1,8}$',
                message=_('Le code doit contenir 1 à 8 chiffres.')
            )
        ]
    )
    
    name = models.CharField(
        _('Nom'),
        max_length=200
    )
    
    account_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=ACCOUNT_TYPES
    )
    
    # Hiérarchie
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Compte parent'),
        related_name='children'
    )
    
    level = models.PositiveIntegerField(
        _('Niveau'),
        default=1
    )
    
    # Configuration
    is_active = models.BooleanField(
        _('Actif'),
        default=True
    )
    
    allow_manual_entries = models.BooleanField(
        _('Autoriser saisie manuelle'),
        default=True
    )
    
    require_analytics = models.BooleanField(
        _('Requiert analytique'),
        default=False
    )
    
    # Société
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        verbose_name=_('Société'),
        related_name='accounts'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Compte')
        verbose_name_plural = _('Comptes')
        ordering = ['code']
        unique_together = ['company', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Calculer le niveau automatiquement."""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        
        super().save(*args, **kwargs)
    
    def get_balance(self, date=None):
        """Obtenir le solde du compte à une date donnée."""
        lines = self.move_lines.all()
        
        if date:
            lines = lines.filter(move__date__lte=date, move__posted=True)
        else:
            lines = lines.filter(move__posted=True)
        
        total_debit = lines.aggregate(total=Sum('debit'))['total'] or Decimal('0.00')
        total_credit = lines.aggregate(total=Sum('credit'))['total'] or Decimal('0.00')
        
        # Selon le type de compte
        if self.account_type in ['asset', 'expense', 'receivable']:
            return total_debit - total_credit
        else:
            return total_credit - total_debit
    
    def get_all_children(self):
        """Obtenir tous les enfants récursivement."""
        children = []
        for child in self.children.all():
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def get_all_parents(self):
        """Obtenir tous les parents récursivement."""
        parents = []
        if self.parent:
            parents.append(self.parent)
            parents.extend(self.parent.get_all_parents())
        return parents
    
    def is_balance_sheet_account(self):
        """Vérifier si c'est un compte de bilan."""
        return self.account_type in ['asset', 'liability', 'equity']
    
    def is_income_statement_account(self):
        """Vérifier si c'est un compte de résultat."""
        return self.account_type in ['income', 'expense']


class Move(models.Model):
    """Modèle pour les écritures comptables."""
    
    # Informations de base
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        verbose_name=_('Journal'),
        related_name='moves'
    )
    
    date = models.DateField(
        _('Date'),
        auto_now_add=True
    )
    
    ref = models.CharField(
        _('Référence'),
        max_length=100,
        blank=True
    )
    
    description = models.TextField(
        _('Libellé'),
        blank=True
    )
    
    # Statut
    posted = models.BooleanField(
        _('Comptabilisé'),
        default=False
    )
    
    posted_at = models.DateTimeField(
        _('Comptabilisé le'),
        null=True,
        blank=True
    )
    
    # Totaux
    total_debit = models.DecimalField(
        _('Total débit'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total_credit = models.DecimalField(
        _('Total crédit'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Origine
    origin_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Type d\'origine')
    )
    
    origin_id = models.PositiveIntegerField(
        _('ID d\'origine'),
        null=True,
        blank=True
    )
    
    # Société
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        verbose_name=_('Société'),
        related_name='moves'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Écriture')
        verbose_name_plural = _('Écritures')
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.journal.code} - {self.date} - {self.ref or self.description[:50]}"
    
    def clean(self):
        """Validation personnalisée."""
        super().clean()
        
        # Vérifier l'équilibre débit/crédit
        if self.total_debit != self.total_credit:
            raise ValidationError({
                'total_debit': _('Le total débit doit être égal au total crédit.')
            })
    
    def post(self):
        """Comptabiliser l'écriture."""
        if self.posted:
            return False
        
        from django.utils import timezone
        
        self.posted = True
        self.posted_at = timezone.now()
        self.save(update_fields=['posted', 'posted_at'])
        
        return True
    
    def unpost(self):
        """Décomptabiliser l'écriture."""
        if not self.posted:
            return False
        
        self.posted = False
        self.posted_at = None
        self.save(update_fields=['posted', 'posted_at'])
        
        return True
    
    def get_origin_object(self):
        """Obtenir l'objet d'origine."""
        if self.origin_type and self.origin_id:
            try:
                return self.origin_type.model_class().objects.get(pk=self.origin_id)
            except:
                return None
        return None


class MoveLine(models.Model):
    """Modèle pour les lignes d'écritures comptables."""
    
    # Écriture
    move = models.ForeignKey(
        Move,
        on_delete=models.CASCADE,
        verbose_name=_('Écriture'),
        related_name='lines'
    )
    
    # Compte
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        verbose_name=_('Compte'),
        related_name='move_lines'
    )
    
    # Partie (client/fournisseur)
    party = models.ForeignKey(
        'crm.Party',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Partie'),
        related_name='move_lines'
    )
    
    # Libellé
    label = models.CharField(
        _('Libellé'),
        max_length=200
    )
    
    # Montants
    debit = models.DecimalField(
        _('Débit'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    credit = models.DecimalField(
        _('Crédit'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Devise
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
    
    # Lettrage
    reconciled_group = models.UUIDField(
        _('Groupe de lettrage'),
        null=True,
        blank=True
    )
    
    reconciled = models.BooleanField(
        _('Lettré'),
        default=False
    )
    
    # Analytique
    analytical_account = models.CharField(
        _('Compte analytique'),
        max_length=50,
        blank=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Ligne d\'écriture')
        verbose_name_plural = _('Lignes d\'écriture')
        ordering = ['id']
    
    def __str__(self):
        return f"{self.account.code} - {self.label} - D:{self.debit} C:{self.credit}"
    
    def clean(self):
        """Validation personnalisée."""
        super().clean()
        
        # Vérifier qu'il y a soit un débit soit un crédit, pas les deux
        if self.debit > 0 and self.credit > 0:
            raise ValidationError({
                'debit': _('Une ligne ne peut pas avoir à la fois un débit et un crédit.')
            })
        
        if self.debit == 0 and self.credit == 0:
            raise ValidationError({
                'debit': _('Une ligne doit avoir soit un débit soit un crédit.')
            })
    
    def get_balance(self):
        """Obtenir le solde de la ligne (débit - crédit)."""
        return self.debit - self.credit
    
    def reconcile(self, group_uuid=None):
        """Lettrer la ligne."""
        if group_uuid is None:
            group_uuid = uuid.uuid4()
        
        self.reconciled_group = group_uuid
        self.reconciled = True
        self.save(update_fields=['reconciled_group', 'reconciled'])
        
        return group_uuid


class VatPeriod(models.Model):
    """Modèle pour les périodes de TVA."""
    
    FREQUENCY_CHOICES = [
        ('monthly', _('Mensuel')),
        ('quarterly', _('Trimestriel')),
    ]
    
    STATUS_CHOICES = [
        ('open', _('Ouvert')),
        ('closed', _('Fermé')),
        ('submitted', _('Soumis')),
    ]
    
    # Informations de base
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        verbose_name=_('Société'),
        related_name='vat_periods'
    )
    
    period_start = models.DateField(
        _('Début de période')
    )
    
    period_end = models.DateField(
        _('Fin de période')
    )
    
    frequency = models.CharField(
        _('Fréquence'),
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='monthly'
    )
    
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    
    # Montants TVA
    vat_collected = models.DecimalField(
        _('TVA collectée'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    vat_deductible = models.DecimalField(
        _('TVA déductible'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    vat_due = models.DecimalField(
        _('TVA à payer'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    vat_credit = models.DecimalField(
        _('Crédit de TVA'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Période TVA')
        verbose_name_plural = _('Périodes TVA')
        ordering = ['-period_start']
        unique_together = ['company', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.company.name} - {self.period_start} à {self.period_end}"
    
    def clean(self):
        """Validation personnalisée."""
        super().clean()
        
        if self.period_start >= self.period_end:
            raise ValidationError({
                'period_end': _('La date de fin doit être postérieure à la date de début.')
            })
    
    def calculate_vat_totals(self):
        """Calculer les totaux TVA de la période."""
        from billing.models import Invoice, DocumentLine
        
        # TVA collectée (factures de vente)
        vat_collected = DocumentLine.objects.filter(
            document__in=Invoice.objects.filter(
                company=self.company,
                invoice_type='sale',
                issue_date__gte=self.period_start,
                issue_date__lte=self.period_end,
                status__in=['validated', 'paid', 'partial']
            )
        ).aggregate(total=Sum('total_line_tva'))['total'] or Decimal('0.00')
        
        # TVA déductible (factures d'achat)
        vat_deductible = DocumentLine.objects.filter(
            document__in=Invoice.objects.filter(
                company=self.company,
                invoice_type='purchase',
                issue_date__gte=self.period_start,
                issue_date__lte=self.period_end,
                status__in=['validated', 'paid', 'partial']
            )
        ).aggregate(total=Sum('total_line_tva'))['total'] or Decimal('0.00')
        
        # Calculer la TVA à payer ou le crédit
        if vat_collected > vat_deductible:
            vat_due = vat_collected - vat_deductible
            vat_credit = Decimal('0.00')
        else:
            vat_due = Decimal('0.00')
            vat_credit = vat_deductible - vat_collected
        
        # Mettre à jour les montants
        self.vat_collected = vat_collected
        self.vat_deductible = vat_deductible
        self.vat_due = vat_due
        self.vat_credit = vat_credit
        
        return {
            'vat_collected': self.vat_collected,
            'vat_deductible': self.vat_deductible,
            'vat_due': self.vat_due,
            'vat_credit': self.vat_credit
        }


class FiscalYear(models.Model):
    """Exercice fiscal, avec clôture et verrouillage de périodes."""
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='fiscal_years',
        verbose_name=_('Société')
    )
    start_date = models.DateField(_('Début'))
    end_date = models.DateField(_('Fin'))
    is_closed = models.BooleanField(_('Clôturé'), default=False)
    locked_until = models.DateField(_('Période verrouillée jusqu\'au'), null=True, blank=True)

    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Exercice fiscal')
        verbose_name_plural = _('Exercices fiscaux')
        unique_together = ['company', 'start_date', 'end_date']
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.company.name} {self.start_date} → {self.end_date}"

    def clean(self):
        super().clean()
        if self.start_date >= self.end_date:
            raise ValidationError({'end_date': _('La date de fin doit être postérieure à la date de début.')})

    def lock_until(self, date_obj):
        self.locked_until = date_obj
        self.save(update_fields=['locked_until'])

    def close(self):
        self.is_closed = True
        self.save(update_fields=['is_closed'])
