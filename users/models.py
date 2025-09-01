"""
Models for users application.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Gestionnaire d'utilisateurs personnalisé."""
    
    def create_user(self, email, username=None, password=None, **extra_fields):
        """Créer un utilisateur normal."""
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username=None, password=None, **extra_fields):
        """Créer un superutilisateur."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """Modèle utilisateur personnalisé."""
    
    # Rôles disponibles
    ROLE_CHOICES = [
        ('admin', _('Administrateur')),
        ('comptable', _('Comptable')),
        ('vente', _('Vente')),
        ('achat', _('Achat')),
        ('lecture', _('Lecture seule')),
    ]
    
    # Champs personnalisés
    email = models.EmailField(_('Adresse email'), unique=True)
    username = models.CharField(
        _('Nom d\'utilisateur'),
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Nom d\'utilisateur optionnel pour la connexion')
    )
    role = models.CharField(
        _('Rôle'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='lecture'
    )
    approval_level = models.PositiveIntegerField(
        _('Niveau d\'approbation'),
        default=1,
        help_text=_('Niveau d\'approbation pour les workflows (1 = basique, 5 = directeur)')
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_('Société'),
        blank=True,
        null=True
    )
    companies = models.ManyToManyField(
        'companies.Company',
        verbose_name=_('Sociétés membres'),
        related_name='users_many',
        blank=True,
        help_text=_('Entreprises auxquelles l\'utilisateur a accès')
    )
    phone = models.CharField(_('Téléphone'), max_length=20, blank=True)
    mfa_enabled = models.BooleanField(_('MFA activé'), default=False)
    mfa_secret = models.CharField(_('Secret MFA'), max_length=32, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    # Configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username est requis pour createsuperuser
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        ordering = ['-date_joined']
    
    def __str__(self):
        if self.username:
            return f"{self.username} ({self.email})"
        return self.email
    
    def get_full_name(self):
        """Retourner le nom complet de l'utilisateur."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return self.username
        return self.email
    
    def get_short_name(self):
        """Retourner le nom court de l'utilisateur."""
        return self.first_name or self.username or self.email
    
    def get_display_name(self):
        """Retourner le nom d'affichage préféré."""
        if self.username:
            return self.username
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.email
    
    def has_role_permission(self, required_role):
        """Vérifier si l'utilisateur a le rôle requis."""
        role_hierarchy = {
            'lecture': 1,
            'achat': 2,
            'vente': 3,
            'comptable': 4,
            'admin': 5
        }
        
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def is_admin(self):
        """Vérifier si l'utilisateur est administrateur."""
        return self.role == 'admin' or self.is_superuser
    
    def is_comptable(self):
        """Vérifier si l'utilisateur est comptable."""
        return self.has_role_permission('comptable')
    
    def is_vente(self):
        """Vérifier si l'utilisateur est en vente."""
        return self.has_role_permission('vente')
    
    def is_achat(self):
        """Vérifier si l'utilisateur est en achat."""
        return self.has_role_permission('achat')
