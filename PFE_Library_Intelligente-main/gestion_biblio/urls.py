from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('livre/<int:id>/', views.detail_livre, name='detail_livre'),
    path('espace/', views.mon_espace, name='mon_espace'),
    path('calculer-retards/', views.calculer_retards, name='calculer_retards'),
    path('reserver/<int:id>/', views.reserver_livre, name='reserver_livre'),
]