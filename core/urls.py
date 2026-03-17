from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('importar/', views.importar_fatura, name='importar_fatura'),
    path('cartoes/', views.gerenciar_cartoes, name='gerenciar_cartoes'),
    path('dividir/<int:transacao_id>/', views.ratear_transacao, name='ratear_transacao'),
    path('extrato/', views.extrato_faturas, name='extrato_faturas'),
]