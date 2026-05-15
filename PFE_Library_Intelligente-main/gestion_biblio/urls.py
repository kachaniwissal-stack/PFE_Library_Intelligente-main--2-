from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # زدت هاد السطر

urlpatterns = [
    path('', views.home, name='home'),
    path('livre/<int:id>/', views.detail_livre, name='detail_livre'),
    path('mon-espace/', views.mon_espace, name='mon_espace'),
    path('reserver/<int:id>/', views.reserver_livre, name='reserver_livre'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.StudentLoginView.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('ajouter-note/<int:id>/', views.ajouter_note, name='ajouter_note'),
    path('chatbot/', views.chatbot_response, name='chatbot_response'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('annuler/<int:emprunt_id>/', views.annuler_reservation, name='annuler_reservation'),
    path('rejoindre-attente/<int:livre_id>/', views.rejoindre_attente, name='rejoindre_attente'),
    path('rejoindre-attente/<int:livre_id>/', views.rejoindre_attente, name='rejoindre_attente'),
    path('chatbot-api/', views.chatbot_response, name='chatbot_api'),
    path('supprimer-note/<int:note_id>/', views.supprimer_note, name='supprimer_note'),

    # --- مسارات استرجاع كلمة المرور اللي زدت ليك أ وصال ---
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='gestion_biblio/password_reset.html'), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='gestion_biblio/password_reset_done.html'), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='gestion_biblio/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='gestion_biblio/password_reset_complete.html'), 
         name='password_reset_complete'),
]