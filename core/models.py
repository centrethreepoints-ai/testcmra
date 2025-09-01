"""
Models for core application.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal


class ApprovalWorkflow(models.Model):
    """Workflow d'approbation pour les documents."""
    
    DOCUMENT_TYPES = [
        ('invoice', _('Facture')),
        ('purchase_order', _('Bon de commande')),
        ('quote', _('Devis')),
        ('payment', _('Paiement')),
        ('journal_entry', _('Écriture comptable')),
        ('general', _('Général')),
    ]
    
    name = models.CharField(_('Nom'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    document_type = models.CharField(_('Type de document'), max_length=50, choices=DOCUMENT_TYPES)
    
    # Niveaux d'approbation
    approval_levels = models.JSONField(
        _('Niveaux d\'approbation'),
        default=list,
        help_text=_('Liste des niveaux avec rôles et seuils')
    )
    
    # Seuils d'approbation
    amount_threshold = models.DecimalField(
        _('Seuil de montant'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Montant au-delà duquel l\'approbation est requise')
    )
    
    # Statut
    active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Workflow d\'approbation')
        verbose_name_plural = _('Workflows d\'approbation')
        unique_together = ['name', 'company']
    
    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"
    
    def get_required_approvals(self, amount=None):
        """Obtenir les approbations requises pour un montant donné."""
        if amount and self.amount_threshold and amount > self.amount_threshold:
            return self.approval_levels
        return []


class ApprovalRequest(models.Model):
    """Demande d'approbation."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('cancelled', _('Annulé')),
    ]
    
    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        verbose_name=_('Workflow'),
        related_name='approval_requests'
    )
    
    # Document à approuver
    document_type = models.CharField(_('Type de document'), max_length=50)
    document_id = models.PositiveIntegerField(_('ID du document'))
    
    # Niveau actuel
    current_level = models.PositiveIntegerField(_('Niveau actuel'), default=1)
    total_levels = models.PositiveIntegerField(_('Total des niveaux'), default=1)
    
    # Statut
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Montant (si applicable)
    amount = models.DecimalField(_('Montant'), max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Notes
    notes = models.TextField(_('Notes'), blank=True)
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='created_approvals')
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Demande d\'approbation')
        verbose_name_plural = _('Demandes d\'approbation')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Approbation {self.workflow.name} - {self.get_status_display()}"
    
    def get_document(self):
        """Obtenir le document associé."""
        from django.contrib.contenttypes.models import ContentType
        try:
            content_type = ContentType.objects.get(model=self.document_type)
            return content_type.model_class().objects.get(pk=self.document_id)
        except (ContentType.DoesNotExist, Exception):
            return None
    
    def can_be_approved_by(self, user):
        """Vérifier si l'utilisateur peut approuver cette demande."""
        if self.status != 'pending':
            return False
        
        # Vérifier le niveau d'approbation
        workflow_levels = self.workflow.approval_levels
        if self.current_level > len(workflow_levels):
            return False
        
        current_level_config = workflow_levels[self.current_level - 1]
        required_roles = current_level_config.get('roles', [])
        
        # Vérifier si l'utilisateur a un des rôles requis
        return user.role in required_roles
    
    def approve(self, user, notes=''):
        """Approuver la demande."""
        if not self.can_be_approved_by(user):
            raise ValidationError(_('Vous ne pouvez pas approuver cette demande.'))
        
        if self.current_level >= self.total_levels:
            # Dernière approbation
            self.status = 'approved'
        else:
            # Passer au niveau suivant
            self.current_level += 1
        
        self.notes = notes
        self.save()
        
        # Créer un log d'approbation
        ApprovalLog.objects.create(
            approval_request=self,
            user=user,
            action='approve',
            notes=notes
        )
    
    def reject(self, user, notes=''):
        """Rejeter la demande."""
        if not self.can_be_approved_by(user):
            raise ValidationError(_('Vous ne pouvez pas rejeter cette demande.'))
        
        self.status = 'rejected'
        self.notes = notes
        self.save()
        
        # Créer un log de rejet
        ApprovalLog.objects.create(
            approval_request=self,
            user=user,
            action='reject',
            notes=notes
        )


class ApprovalLog(models.Model):
    """Log des actions d'approbation."""
    
    ACTION_CHOICES = [
        ('approve', _('Approbation')),
        ('reject', _('Rejet')),
        ('cancel', _('Annulation')),
        ('comment', _('Commentaire')),
    ]
    
    approval_request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        verbose_name=_('Demande d\'approbation'),
        related_name='logs'
    )
    
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        verbose_name=_('Utilisateur'),
        related_name='approval_logs'
    )
    
    action = models.CharField(_('Action'), max_length=20, choices=ACTION_CHOICES)
    notes = models.TextField(_('Notes'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Log d\'approbation')
        verbose_name_plural = _('Logs d\'approbation')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_action_display()} - {self.created_at}"


class DashboardWidget(models.Model):
    """Widget personnalisable pour le tableau de bord."""
    
    WIDGET_TYPES = [
        ('kpi', _('Indicateur clé')),
        ('chart', _('Graphique')),
        ('table', _('Tableau')),
        ('list', _('Liste')),
        ('gauge', _('Jauge')),
        ('progress', _('Barre de progression')),
    ]
    
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        verbose_name=_('Utilisateur'),
        related_name='dashboard_widgets'
    )
    
    widget_type = models.CharField(_('Type de widget'), max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(_('Titre'), max_length=100)
    
    # Position et taille
    position = models.JSONField(
        _('Position'),
        default=dict,
        help_text=_('Position x, y, width, height')
    )
    
    # Configuration
    settings = models.JSONField(
        _('Paramètres'),
        default=dict,
        help_text=_('Configuration spécifique au widget')
    )
    
    # Statut
    active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Widget du tableau de bord')
        verbose_name_plural = _('Widgets du tableau de bord')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"
    
    def get_default_position(self):
        """Obtenir la position par défaut."""
        return {
            'x': 0,
            'y': 0,
            'width': 6,
            'height': 4
        }
    
    def save(self, *args, **kwargs):
        """Définir la position par défaut si pas définie."""
        if not self.position:
            self.position = self.get_default_position()
        super().save(*args, **kwargs)


class Notification(models.Model):
    """Système de notifications."""
    
    NOTIFICATION_TYPES = [
        ('info', _('Information')),
        ('success', _('Succès')),
        ('warning', _('Avertissement')),
        ('error', _('Erreur')),
        ('approval', _('Approbation')),
        ('reminder', _('Rappel')),
        ('system', _('Système')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Faible')),
        ('normal', _('Normale')),
        ('high', _('Élevée')),
        ('urgent', _('Urgente')),
    ]
    
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        verbose_name=_('Utilisateur'),
        related_name='notifications'
    )
    
    title = models.CharField(_('Titre'), max_length=200)
    message = models.TextField(_('Message'))
    notification_type = models.CharField(_('Type'), max_length=20, choices=NOTIFICATION_TYPES, default='info')
    priority = models.CharField(_('Priorité'), max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Lien d'action
    action_url = models.CharField(_('URL d\'action'), max_length=200, blank=True)
    action_text = models.CharField(_('Texte de l\'action'), max_length=100, blank=True)
    
    # Statut
    read = models.BooleanField(_('Lu'), default=False)
    dismissed = models.BooleanField(_('Rejeté'), default=False)
    
    # Métadonnées
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        verbose_name=_('Créé par'),
        related_name='created_notifications',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    read_at = models.DateTimeField(_('Lu le'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"
    
    def mark_as_read(self):
        """Marquer la notification comme lue."""
        from django.utils import timezone
        self.read = True
        self.read_at = timezone.now()
        self.save(update_fields=['read', 'read_at'])
    
    def dismiss(self):
        """Rejeter la notification."""
        self.dismissed = True
        self.save(update_fields=['dismissed'])
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type='info', 
                          priority='normal', action_url='', action_text='', 
                          company=None, created_by=None):
        """Créer une nouvelle notification."""
        if not company:
            company = user.company
        
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            action_text=action_text,
            company=company,
            created_by=created_by
        )
