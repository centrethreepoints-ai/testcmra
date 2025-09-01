"""
Forms for users application.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from .models import User


class CustomAuthenticationForm(AuthenticationForm):
    """Formulaire d'authentification personnalisé acceptant email ou username."""
    
    username = forms.CharField(
        label=_('Email ou nom d\'utilisateur'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email ou nom d\'utilisateur',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label=_('Mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe',
            'autocomplete': 'current-password'
        })
    )
    
    def clean(self):
        """Valider les identifiants de connexion."""
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Essayer d'abord avec l'email
            user = authenticate(self.request, username=username, password=password)
            
            # Si ça ne marche pas, essayer avec le username
            if user is None:
                try:
                    # Chercher l'utilisateur par username
                    user_obj = User.objects.get(username=username)
                    user = authenticate(self.request, username=user_obj.email, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is None:
                raise forms.ValidationError(
                    _('Email/nom d\'utilisateur ou mot de passe incorrect.')
                )
            else:
                self.confirm_login_allowed(user)
                # Stocker l'utilisateur pour get_user()
                self.user_cache = user
        
        return self.cleaned_data


class UserUpdateForm(forms.ModelForm):
    """Formulaire de mise à jour du profil utilisateur."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'phone', 'role']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Empêcher la modification du rôle pour les utilisateurs non-admin
        if self.instance and not self.instance.is_superuser:
            if 'role' in self.fields:
                self.fields['role'].disabled = True
                self.fields['role'].help_text = _("Seul un administrateur peut modifier le rôle.")
        
        # Ajouter des placeholders et labels
        self.fields['username'].help_text = _("Nom d'utilisateur optionnel pour la connexion")
        self.fields['username'].required = False
    
    def clean_username(self):
        """Valider l'unicité du username."""
        username = self.cleaned_data.get('username')
        if username:
            # Vérifier que le username est unique
            existing_user = User.objects.filter(username=username).exclude(pk=self.instance.pk if self.instance else None)
            if existing_user.exists():
                raise forms.ValidationError(_("Ce nom d'utilisateur est déjà utilisé."))
        return username


class UserCreationForm(DjangoUserCreationForm):
    """Formulaire de création d'utilisateur."""
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'role', 'company']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs de mot de passe optionnels pour l'admin
        if 'password1' in self.fields:
            self.fields['password1'].required = False
            self.fields['password1'].help_text = _("Laissez vide pour générer un mot de passe automatiquement.")
        if 'password2' in self.fields:
            self.fields['password2'].required = False
        
        # Ajouter des placeholders et labels
        self.fields['username'].help_text = _("Nom d'utilisateur optionnel pour la connexion")
        self.fields['username'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Les nouveaux mots de passe ne correspondent pas."))
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if not self.cleaned_data.get('password1'):
            # Générer un mot de passe aléatoire si aucun n'est fourni
            import random
            import string
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            user.set_password(password)
        if commit:
            user.save()
        return user


class PasswordChangeForm(forms.Form):
    """Formulaire de changement de mot de passe."""
    
    old_password = forms.CharField(
        label=_('Ancien mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ancien mot de passe'
        })
    )
    new_password1 = forms.CharField(
        label=_('Nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        })
    )
    new_password2 = forms.CharField(
        label=_('Confirmer le nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le nouveau mot de passe'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        """Valider l'ancien mot de passe."""
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(_("L'ancien mot de passe est incorrect."))
        return old_password
    
    def clean_new_password2(self):
        """Valider la confirmation du nouveau mot de passe."""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(_("Les nouveaux mots de passe ne correspondent pas."))
        return password2
    
    def save(self, commit=True):
        """Sauvegarder le nouveau mot de passe."""
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user


class AdminSetPasswordForm(forms.Form):
    """Formulaire pour que l'admin définisse le mot de passe d'un utilisateur sans ancien mot de passe."""
    new_password1 = forms.CharField(
        label=_('Nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nouveau mot de passe'})
    )
    new_password2 = forms.CharField(
        label=_('Confirmer le nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmer le nouveau mot de passe'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_('Les nouveaux mots de passe ne correspondent pas.'))
        return cleaned_data
