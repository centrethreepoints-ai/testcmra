"""
Views for users application.
"""

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import User
from .forms import (
    UserUpdateForm,
    CustomAuthenticationForm,
    UserCreationForm,
    AdminSetPasswordForm,
)


def login_view(request):
    """Vue de connexion."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Récupérer les données du formulaire
            identifier = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Utiliser le backend d'authentification personnalisé
            user = authenticate(request, username=identifier, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue {user.get_display_name()} !')
                next_url = request.GET.get('next', 'core:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Email/nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    """Vue de déconnexion."""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('users:login')


@login_required
def change_password_view(request):
    """Vue de changement de mot de passe."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre mot de passe a été modifié avec succès.')
            return redirect('core:dashboard')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class UserProfileView(UpdateView):
    """Vue de profil utilisateur."""
    model = User
    form_class = UserUpdateForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('dashboard')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profil mis à jour avec succès.')
        return super().form_valid(form)


@login_required
def user_list(request):
    """Liste des utilisateurs (admin seulement)."""
    if request.user.role != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    
    users = User.objects.filter(company=request.user.company).order_by('-date_joined')
    return render(request, 'users/user_list.html', {'users': users})


@login_required
def user_detail(request, pk):
    """Détail d'un utilisateur (admin seulement)."""
    if request.user.role != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    user_obj = User.objects.filter(company=request.user.company, pk=pk).first()
    if not user_obj:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('users:user_list')
    return render(request, 'users/user_detail.html', {'user_obj': user_obj})


@login_required
def user_create(request):
    """Création d'utilisateur (admin seulement)."""
    if request.user.role != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            messages.success(request, 'Utilisateur créé avec succès.')
            return redirect('users:user_detail', pk=new_user.pk)
    else:
        form = UserCreationForm(initial={'company': request.user.company})
    return render(request, 'users/user_form.html', {'form': form, 'mode': 'create'})


@login_required
def user_edit(request, pk):
    """Édition d'utilisateur (admin seulement)."""
    if request.user.role != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    user_obj = User.objects.filter(company=request.user.company, pk=pk).first()
    if not user_obj:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('users:user_list')
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Utilisateur mis à jour avec succès.')
            return redirect('users:user_detail', pk=user_obj.pk)
    else:
        form = UserUpdateForm(instance=user_obj)
    return render(request, 'users/user_form.html', {'form': form, 'mode': 'edit', 'user_obj': user_obj})


@login_required
def user_set_password(request, pk):
    """Permettre à un administrateur de définir le mot de passe d'un utilisateur."""
    if request.user.role != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    user_obj = User.objects.filter(company=request.user.company, pk=pk).first()
    if not user_obj:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('users:user_list')
    if request.method == 'POST':
        form = AdminSetPasswordForm(request.POST)
        if form.is_valid():
            user_obj.set_password(form.cleaned_data['new_password1'])
            user_obj.save(update_fields=['password'])
            messages.success(request, 'Mot de passe défini avec succès.')
            return redirect('users:user_detail', pk=user_obj.pk)
    else:
        form = AdminSetPasswordForm()
    return render(request, 'users/user_set_password.html', {'form': form, 'user_obj': user_obj})


@login_required
def user_delete(request, pk):
    """Suppression d'utilisateur (admin seulement)."""
    if request.user.role != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    user_obj = User.objects.filter(company=request.user.company, pk=pk).first()
    if not user_obj:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('users:user_list')
    if request.method == 'POST':
        if user_obj == request.user:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect('users:user_detail', pk=user_obj.pk)
        user_obj.delete()
        messages.success(request, 'Utilisateur supprimé.')
        return redirect('users:user_list')
    return render(request, 'users/user_confirm_delete.html', {'user_obj': user_obj})
