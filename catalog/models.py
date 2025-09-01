"""
Models for catalog application.
"""

from django.db import models
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from simple_history.models import HistoricalRecords
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import JSONField


class Category(models.Model):
    """Catégorie de produits."""
    
    name = models.CharField(_('Nom'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')
        unique_together = ['name', 'company']
    
    def __str__(self):
        return self.name
    history = HistoricalRecords()


class TaxRate(models.Model):
    """Taux de TVA."""
    
    name = models.CharField(_('Nom'), max_length=50)
    rate = models.DecimalField(_('Taux (%)'), max_digits=5, decimal_places=2)
    # Some existing databases still have a NOT NULL 'code' column; keep a compatible field
    code = models.CharField(_('Code'), max_length=100, blank=True, default='')
    # Some existing databases still have a NOT NULL 'description' column; keep a compatible field
    description = models.TextField(_('Description'), blank=True, default='')
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(_('Actif'), default=True)  # Keep original name for compatibility
    # Keep legacy timestamps for compatibility with older databases
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Taux de TVA')
        verbose_name_plural = _('Taux de TVA')
        unique_together = ['rate', 'company']
    
    def __str__(self):
        return f"{self.name} ({self.rate}%)"
    
    def get_rate_decimal(self):
        """Obtenir le taux en décimal (ex: 20% -> 0.20)."""
        return self.rate / Decimal('100.00')


class Product(models.Model):
    """Produit ou service."""
    
    PRODUCT_TYPES = [
        ('product', _('Produit')),
        ('service', _('Service')),
    ]
    
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True)
    product_type = models.CharField(_('Type'), max_length=20, choices=PRODUCT_TYPES, default='product')
    
    # Prix et TVA
    price_ht = models.DecimalField(_('Prix HT'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.ForeignKey(TaxRate, on_delete=models.PROTECT, null=True, blank=True)
    
    # Stock (pour les produits physiques)
    has_stock = models.BooleanField(_('Gestion de stock'), default=False)
    current_stock = models.IntegerField(_('Stock actuel'), default=0)
    min_stock = models.PositiveIntegerField(_('Stock minimum'), default=0)
    max_stock = models.PositiveIntegerField(_('Stock maximum'), default=1000)
    
    # Références
    # Some databases still have a legacy NOT NULL 'code' column; keep it in sync with 'sku'.
    code = models.CharField(_('Code'), max_length=100, default='', blank=True)
    sku = models.CharField(_('Référence'), max_length=100, blank=True)
    barcode = models.CharField(_('Code-barres'), max_length=100, blank=True)
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)  # Keep original name for compatibility
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Produit')
        verbose_name_plural = _('Produits')
        unique_together = ['sku', 'company']
    
    def __str__(self):
        return self.name
    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        # Ensure SKU uniqueness per company; auto-generate if missing/blank
        if not getattr(self, 'sku', None) or not str(self.sku).strip():
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            base = f"P-{timestamp}"
            candidate = base
            # company may be unset on first pass; save after assigning company in views
            if getattr(self, 'company_id', None):
                suffix = 0
                while Product.objects.filter(company_id=self.company_id, sku=candidate).exists():
                    suffix += 1
                    candidate = f"{base}-{suffix}"
            self.sku = candidate
        # Keep legacy 'code' column synchronized with 'sku' if empty
        if (not getattr(self, 'code', '') or not str(self.code).strip()) and getattr(self, 'sku', ''):
            self.code = self.sku
        super().save(*args, **kwargs)

    def get_price_ttc(self):
        """Obtenir le prix TTC."""
        if self.tax_rate:
            return self.price_ht * (1 + self.tax_rate.get_rate_decimal())
        return self.price_ht
    
    def is_low_stock(self):
        """Vérifier si le stock est bas."""
        if not self.has_stock:
            return False
        return self.current_stock <= self.min_stock
    
    def is_out_of_stock(self):
        """Vérifier si le produit est en rupture de stock."""
        if not self.has_stock:
            return False
        return self.current_stock <= 0


class StockMovement(models.Model):
    """Mouvement de stock."""
    
    MOVEMENT_TYPES = [
        ('in', _('Entrée')),
        ('out', _('Sortie')),
        ('adjustment', _('Ajustement')),
        ('transfer', _('Transfert')),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(_('Type'), max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.PositiveIntegerField(_('Quantité'))
    unit_cost = models.DecimalField(_('Coût unitaire'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    reference = models.CharField(_('Référence'), max_length=100, blank=True)  # Invoice/PO number
    reference_type = models.CharField(_('Type de référence'), max_length=50, blank=True)  # 'invoice', 'po', 'adjustment'
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Stock avant et après
    stock_before = models.IntegerField(_('Stock avant'))
    stock_after = models.IntegerField(_('Stock après'))
    
    # Notes
    notes = models.TextField(_('Notes'), blank=True)
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey('users.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Mouvement de stock')
        verbose_name_plural = _('Mouvements de stock')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} ({self.quantity})"
    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        """Mettre à jour le stock du produit."""
        if not self.pk:  # Nouveau mouvement
            # Assurer un stock_before cohérent
            if self.stock_before is None:
                # Sécuriser en cas de valeur None exceptionnelle
                self.stock_before = int(getattr(self.product, 'current_stock', 0) or 0)

            # Calculer le stock après selon le type
            if self.movement_type == 'in':
                self.stock_after = int(self.stock_before) + int(self.quantity)
            elif self.movement_type == 'out':
                self.stock_after = int(self.stock_before) - int(self.quantity)
            elif self.movement_type == 'adjustment':
                self.stock_after = int(self.quantity)
            elif self.movement_type == 'transfer':
                # Pas de changement de stock global pour un transfert simple (sans multi-emplacements)
                self.stock_after = int(self.stock_before)
            else:
                # Par défaut, ne pas modifier le stock
                self.stock_after = int(self.stock_before)
            
            # Mettre à jour le stock du produit
            self.product.current_stock = self.stock_after
            self.product.save(update_fields=['current_stock'])
            # Average cost valuation if enabled at company level
            try:
                company = getattr(self, 'company', None)
                if company and company.get_preference('feature_stock_avg_cost_enabled', True):
                    # Update average cost on IN movements only
                    if self.movement_type == 'in':
                        stock_before_qty = int(self.stock_before or 0)
                        stock_after_qty = int(self.stock_after or 0)
                        if stock_after_qty > 0:
                            previous_total_value = (getattr(self.product, 'price_ht', Decimal('0.00')) * stock_before_qty)
                            incoming_value = (self.unit_cost or Decimal('0.00')) * Decimal(self.quantity)
                            new_avg_cost = (previous_total_value + incoming_value) / Decimal(stock_after_qty)
                            # Store as price_ht baseline cost for margin computation
                            self.product.price_ht = new_avg_cost.quantize(Decimal('0.01'))
                            self.product.save(update_fields=['price_ht'])
            except Exception:
                pass
        
        super().save(*args, **kwargs)


class ProductStock(models.Model):
    """Stock actuel d'un produit."""
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock_info')
    current_stock = models.IntegerField(_('Stock actuel'), default=0)
    min_stock = models.PositiveIntegerField(_('Stock minimum'), default=0)
    max_stock = models.PositiveIntegerField(_('Stock maximum'), default=1000)
    average_cost = models.DecimalField(_('Coût moyen'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(_('Dernière mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('Stock produit')
        verbose_name_plural = _('Stocks produits')
    
    def __str__(self):
        return f"Stock {self.product.name}: {self.current_stock}"
    history = HistoricalRecords()
    
    def is_low_stock(self):
        """Vérifier si le stock est bas."""
        return self.current_stock <= self.min_stock
    
    def is_out_of_stock(self):
        """Vérifier si le produit est en rupture de stock."""
        return self.current_stock <= 0
    
    def get_stock_status(self):
        """Obtenir le statut du stock."""
        if self.is_out_of_stock():
            return 'out_of_stock'
        elif self.is_low_stock():
            return 'low_stock'
        else:
            return 'normal'



class InventorySession(models.Model):
    """Session d'inventaire avec snapshot et options."""

    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('active', _('En cours')),
        ('closed', _('Clôturé')),
    ]

    SCOPE_CHOICES = [
        ('all', _('Tous les produits')),
        ('category', _('Catégorie')),
    ]

    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    name = models.CharField(_('Nom de la session'), max_length=120)
    scope_type = models.CharField(_('Périmètre'), max_length=20, choices=SCOPE_CHOICES, default='all')
    category = models.ForeignKey('catalog.Category', on_delete=models.SET_NULL, null=True, blank=True)

    is_blind = models.BooleanField(_('Comptage à l’aveugle'), default=False)
    freeze_stock = models.BooleanField(_('Geler mouvements pendant inventaire'), default=False)
    tolerance_percent = models.DecimalField(_('Tolérance %'), max_digits=5, decimal_places=2, default=Decimal('0.00'))

    snapshot = JSONField(_('Snapshot de départ'), default=dict, blank=True)

    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='draft')
    started_at = models.DateTimeField(_('Démarré le'), null=True, blank=True)
    ended_at = models.DateTimeField(_('Clôturé le'), null=True, blank=True)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='inventory_created')
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Session d\'inventaire')
        verbose_name_plural = _('Sessions d\'inventaire')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.name} ({self.get_status_display()})"

    def should_include_product(self, product: 'Product') -> bool:
        if self.scope_type == 'category' and self.category_id:
            return product.category_id == self.category_id
        return True

    def compute_progress(self):
        total = self.counts.count()
        if total == 0:
            return {'total': 0, 'counted': 0, 'validated': 0, 'percent': 0}
        counted = self.counts.exclude(counted_qty__isnull=True).count()
        validated = self.counts.filter(status='validated').count()
        percent = int((counted / total) * 100)
        return {'total': total, 'counted': counted, 'validated': validated, 'percent': percent}


class InventoryCount(models.Model):
    """Ligne de comptage d'une session d'inventaire."""

    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('counted', _('Compté')),
        ('validated', _('Validé')),
        ('flagged', _('Recomptage')),
    ]

    session = models.ForeignKey(InventorySession, on_delete=models.CASCADE, related_name='counts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    snapshot_qty = models.IntegerField(_('Stock au départ'), default=0)
    counted_qty = models.IntegerField(_('Quantité comptée'), null=True, blank=True)
    recounted_qty = models.IntegerField(_('Recomptage'), null=True, blank=True)
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_assigned')
    zone = models.CharField(_('Zone/Emplacement'), max_length=64, blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Comptage d\'inventaire')
        verbose_name_plural = _('Comptages d\'inventaire')
        unique_together = ['session', 'product']

    def variance(self) -> int:
        current = self.recounted_qty if self.recounted_qty is not None else (self.counted_qty if self.counted_qty is not None else None)
        if current is None:
            return 0
        return int(current) - int(self.snapshot_qty)

    
