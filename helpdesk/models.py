from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model


class SLA(models.Model):
    name = models.CharField(_('Nom'), max_length=100)
    response_time_hours = models.PositiveIntegerField(_('Temps de réponse (h)'), default=8)
    resolution_time_hours = models.PositiveIntegerField(_('Temps de résolution (h)'), default=72)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    active = models.BooleanField(_('Actif'), default=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('SLA')
        verbose_name_plural = _('SLAs')

    def __str__(self):
        return self.name


class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ('low', _('Faible')),
        ('normal', _('Normale')),
        ('high', _('Élevée')),
        ('urgent', _('Urgente')),
    ]
    STATUS_CHOICES = [
        ('new', _('Nouveau')),
        ('open', _('Ouvert')),
        ('pending', _('En attente')),
        ('resolved', _('Résolu')),
        ('closed', _('Fermé')),
    ]

    number = models.CharField(_('Numéro'), max_length=30, unique=True)
    title = models.CharField(_('Titre'), max_length=200)
    description = models.TextField(_('Description'))
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(_('Priorité'), max_length=20, choices=PRIORITY_CHOICES, default='normal')
    sla = models.ForeignKey(SLA, on_delete=models.SET_NULL, null=True, blank=True)
    requester = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='requested_tickets')
    assignee = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    due_at = models.DateTimeField(_('Échéance'), null=True, blank=True)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.number} - {self.title}"


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    message = models.TextField(_('Message'))
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('Commentaire')
        verbose_name_plural = _('Commentaires')
        ordering = ['created_at']


