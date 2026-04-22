from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('livre/<int:id>/', views.detail_livre, name='detail_livre'),
    path('mon-espace/', views.mon_espace, name='mon_espace'),
    path('reserver/<int:id>/', views.reserver_livre, name='reserver_livre'),
    path('dashboard/', views.dashboard, name='dashboard'), # الرابط الجديد
    path('chatbot/', views.chatbot_response, name='chatbot_response'),
]