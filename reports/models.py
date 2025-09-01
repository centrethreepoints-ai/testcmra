"""
Models for reports application.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from decimal import Decimal


class ReportSchedule(models.Model):
    """Planification des rapports automatiques."""
    
    FREQUENCY_CHOICES = [
        ('daily', _('Quotidien')),
        ('weekly', _('Hebdomadaire')),
        ('monthly', _('Mensuel')),
        ('quarterly', _('Trimestriel')),
        ('yearly', _('Annuel')),
    ]
    
    REPORT_TYPE_CHOICES = [
        ('trial_balance', _('Balance des comptes')),
        ('general_ledger', _('Grand livre')),
        ('vat_return', _('Déclaration TVA')),
        ('ar_ap', _('Aged receivables/payables')),
        ('cash_flow', _('État des flux de trésorerie')),
        ('profit_loss', _('Compte de résultat')),
        ('balance_sheet', _('Bilan')),
        ('inventory_report', _('Rapport d\'inventaire')),
        ('sales_report', _('Rapport des ventes')),
        ('custom', _('Rapport personnalisé')),
    ]
    
    name = models.CharField(_('Nom'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    report_type = models.CharField(_('Type de rapport'), max_length=50, choices=REPORT_TYPE_CHOICES)
    
    # Planification
    frequency = models.CharField(_('Fréquence'), max_length=20, choices=FREQUENCY_CHOICES)
    day_of_week = models.PositiveSmallIntegerField(_('Jour de la semaine (0-6, 0=Lundi)'), null=True, blank=True)
    day_of_month = models.PositiveSmallIntegerField(_('Jour du mois (1-31)'), null=True, blank=True)
    month = models.PositiveSmallIntegerField(_('Mois (1-12)'), null=True, blank=True)
    
    # Destinataires
    recipients = models.JSONField(_('Destinataires'), default=list, help_text=_('Liste des adresses email'))
    cc_recipients = models.JSONField(_('Destinataires en copie'), default=list, blank=True)
    
    # Paramètres du rapport
    parameters = models.JSONField(_('Paramètres'), default=dict, blank=True, help_text=_('Paramètres spécifiques au rapport'))
    
    # Statut
    active = models.BooleanField(_('Actif'), default=True)
    last_run = models.DateTimeField(_('Dernière exécution'), null=True, blank=True)
    next_run = models.DateTimeField(_('Prochaine exécution'), null=True, blank=True)
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Planification de rapport')
        verbose_name_plural = _('Planifications de rapports')
        unique_together = ['name', 'company']
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"
    
    def get_next_run_date(self):
        """Calculer la prochaine date d'exécution."""
        from django.utils import timezone
        from datetime import timedelta
        import calendar
        
        now = timezone.now()
        
        if self.frequency == 'daily':
            return now + timedelta(days=1)
        elif self.frequency == 'weekly':
            if self.day_of_week is not None:
                days_ahead = self.day_of_week - now.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return now + timedelta(days=days_ahead)
        elif self.frequency == 'monthly':
            if self.day_of_month is not None:
                # Find next month with this day
                current_month = now.month
                current_year = now.year
                
                # Try current month
                try:
                    next_date = now.replace(day=self.day_of_month)
                    if next_date <= now:
                        # Move to next month
                        if current_month == 12:
                            current_month = 1
                            current_year += 1
                        else:
                            current_month += 1
                        next_date = now.replace(year=current_year, month=current_month, day=self.day_of_month)
                    return next_date
                except ValueError:
                    # Invalid day for month, move to next month
                    pass
        elif self.frequency == 'quarterly':
            # Quarterly reports (every 3 months)
            return now + timedelta(days=90)
        elif self.frequency == 'yearly':
            if self.month is not None and self.day_of_month is not None:
                # Try current year
                try:
                    next_date = now.replace(month=self.month, day=self.day_of_month)
                    if next_date <= now:
                        next_date = next_date.replace(year=next_date.year + 1)
                    return next_date
                except ValueError:
                    pass
        
        # Default: next day
        return now + timedelta(days=1)


class CashFlowStatement(models.Model):
    """État des flux de trésorerie."""
    
    PERIOD_TYPES = [
        ('monthly', _('Mensuel')),
        ('quarterly', _('Trimestriel')),
        ('yearly', _('Annuel')),
    ]
    
    period_type = models.CharField(_('Type de période'), max_length=20, choices=PERIOD_TYPES)
    start_date = models.DateField(_('Date de début'))
    end_date = models.DateField(_('Date de fin'))
    
    # Flux d'exploitation
    operating_cash_flow = models.DecimalField(_('Flux d\'exploitation'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Flux d'investissement
    investing_cash_flow = models.DecimalField(_('Flux d\'investissement'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Flux de financement
    financing_cash_flow = models.DecimalField(_('Flux de financement'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Variation de trésorerie
    net_cash_change = models.DecimalField(_('Variation nette de trésorerie'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Trésorerie d'ouverture et de clôture
    opening_cash = models.DecimalField(_('Trésorerie d\'ouverture'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    closing_cash = models.DecimalField(_('Trésorerie de clôture'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('État des flux de trésorerie')
        verbose_name_plural = _('États des flux de trésorerie')
        unique_together = ['company', 'period_type', 'start_date', 'end_date']
        ordering = ['-end_date']
    
    def __str__(self):
        return f"Flux de trésorerie {self.start_date} - {self.end_date}"
    
    def calculate_net_cash_change(self):
        """Calculer la variation nette de trésorerie."""
        self.net_cash_change = (
            self.operating_cash_flow + 
            self.investing_cash_flow + 
            self.financing_cash_flow
        )
        return self.net_cash_change
    
    def calculate_closing_cash(self):
        """Calculer la trésorerie de clôture."""
        self.closing_cash = self.opening_cash + self.net_cash_change
        return self.closing_cash


class AgingReport(models.Model):
    """Rapport de vieillissement des créances/dettes."""
    
    REPORT_TYPES = [
        ('receivables', _('Créances clients')),
        ('payables', _('Dettes fournisseurs')),
    ]
    
    report_type = models.CharField(_('Type de rapport'), max_length=20, choices=REPORT_TYPES)
    report_date = models.DateField(_('Date du rapport'))
    
    # Périodes de vieillissement
    current_amount = models.DecimalField(_('Montant à échéance'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    days_30_amount = models.DecimalField(_('30 jours'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    days_60_amount = models.DecimalField(_('60 jours'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    days_90_amount = models.DecimalField(_('90 jours'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    days_120_amount = models.DecimalField(_('120 jours'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    over_120_amount = models.DecimalField(_('Plus de 120 jours'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Total
    total_amount = models.DecimalField(_('Total'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Rapport de vieillissement')
        verbose_name_plural = _('Rapports de vieillissement')
        unique_together = ['company', 'report_type', 'report_date']
        ordering = ['-report_date']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.report_date}"
    
    def calculate_total(self):
        """Calculer le total des montants."""
        self.total_amount = (
            self.current_amount + 
            self.days_30_amount + 
            self.days_60_amount + 
            self.days_90_amount + 
            self.days_120_amount + 
            self.over_120_amount
        )
        return self.total_amount
    
    def get_aging_percentages(self):
        """Obtenir les pourcentages de vieillissement."""
        if self.total_amount == 0:
            return {}
        
        return {
            'current': (self.current_amount / self.total_amount) * 100,
            'days_30': (self.days_30_amount / self.total_amount) * 100,
            'days_60': (self.days_60_amount / self.total_amount) * 100,
            'days_90': (self.days_90_amount / self.total_amount) * 100,
            'days_120': (self.days_120_amount / self.total_amount) * 100,
            'over_120': (self.over_120_amount / self.total_amount) * 100,
        }


class ProfitLossStatement(models.Model):
    """Compte de résultat."""
    
    PERIOD_TYPES = [
        ('monthly', _('Mensuel')),
        ('quarterly', _('Trimestriel')),
        ('yearly', _('Annuel')),
    ]
    
    period_type = models.CharField(_('Type de période'), max_length=20, choices=PERIOD_TYPES)
    start_date = models.DateField(_('Date de début'))
    end_date = models.DateField(_('Date de fin'))
    
    # Produits
    revenue = models.DecimalField(_('Chiffre d\'affaires'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    other_income = models.DecimalField(_('Autres produits'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_income = models.DecimalField(_('Total des produits'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Charges
    cost_of_sales = models.DecimalField(_('Coût des ventes'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    operating_expenses = models.DecimalField(_('Charges d\'exploitation'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    financial_expenses = models.DecimalField(_('Charges financières'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    exceptional_expenses = models.DecimalField(_('Charges exceptionnelles'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_expenses = models.DecimalField(_('Total des charges'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Résultat
    operating_profit = models.DecimalField(_('Résultat d\'exploitation'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    financial_result = models.DecimalField(_('Résultat financier'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    exceptional_result = models.DecimalField(_('Résultat exceptionnel'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_profit = models.DecimalField(_('Résultat net'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Compte de résultat')
        verbose_name_plural = _('Comptes de résultat')
        unique_together = ['company', 'period_type', 'start_date', 'end_date']
        ordering = ['-end_date']
    
    def __str__(self):
        return f"Compte de résultat {self.start_date} - {self.end_date}"
    
    def calculate_totals(self):
        """Calculer tous les totaux."""
        # Total des produits
        self.total_income = self.revenue + self.other_income
        
        # Total des charges
        self.total_expenses = (
            self.cost_of_sales + 
            self.operating_expenses + 
            self.financial_expenses + 
            self.exceptional_expenses
        )
        
        # Résultats
        self.operating_profit = self.revenue - self.cost_of_sales - self.operating_expenses
        self.financial_result = self.operating_profit - self.financial_expenses
        self.exceptional_result = self.financial_result - self.exceptional_expenses
        self.net_profit = self.exceptional_result
        
        return {
            'total_income': self.total_income,
            'total_expenses': self.total_expenses,
            'operating_profit': self.operating_profit,
            'financial_result': self.financial_result,
            'exceptional_result': self.exceptional_result,
            'net_profit': self.net_profit,
        }
