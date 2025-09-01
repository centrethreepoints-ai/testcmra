from django.urls import path
from . import views

app_name = 'helpdesk'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('<int:pk>/comment/', views.ticket_comment, name='ticket_comment'),
    path('my/', views.my_ticket_list, name='my_ticket_list'),
    path('slas/', views.sla_list, name='sla_list'),
    path('slas/create/', views.sla_create, name='sla_create'),
]


