"""
URLs for users application.
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('list/', views.user_list, name='user_list'),
    path('<int:pk>/', views.user_detail, name='user_detail'),
    path('create/', views.user_create, name='user_create'),
    path('<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('<int:pk>/set-password/', views.user_set_password, name='user_set_password'),
]

# URLs à la racine pour l'authentification
urlpatterns += [
    path('', views.login_view, name='login_root'),
]
