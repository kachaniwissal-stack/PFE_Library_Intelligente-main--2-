from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from gestion_biblio.models import Emprunt

class Command(BaseCommand):
    help = 'Gère les rappels de délai (aujourd’hui) et les alertes de retard (une seule fois)'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(f"Vérification du : {today}")

        # --- 1. تذكير بآخر أجل (اليوم) ---
        # كيتصيفط مرة وحدة حيت كنستعملو alerte_envoyee
        rappels = Emprunt.objects.filter(date_retour_prevue=today, statut='en cours', alerte_envoyee=False)
        for emp in rappels:
            self.envoyer_email(emp, "⏳ Rappel : Dernier délai aujourd'hui", 
                               f"Bonjour {emp.etudiant.user.first_name}, c'est aujourd'hui le dernier délai pour rendre '{emp.exemplaire.livre.titre}'.")
            emp.alerte_envoyee = True
            emp.save()

        # --- 2. إنذار التأخير (كيتصيفط غير مرة وحدة) ---
        # كنقلبو غير على اللي تاريخهم فات (lt = less than) والـ statut ديالهم مازال 'en cours'
        retards_nouveaux = Emprunt.objects.filter(date_retour_prevue__lt=today, statut='en cours')
        
        for emp in retards_nouveaux:
            # كنحسبو الغرامة
            diff = today - emp.date_retour_prevue
            jours = diff.days
            emp.amende = jours * 5
            
            # مـهـم: كنبدلو الـ statut لـ 'en retard' باش المرة الجاية مايلقاهش السكريبت ومايصيفطش ليه
            emp.statut = 'en retard'
            emp.save()

            # صيفط الإيميل
            subject = f"🚨 ALERTE RETARD : {emp.exemplaire.livre.titre}"
            message = f"Bonjour {emp.etudiant.user.first_name},\n\nVous avez dépassé le délai pour le livre '{emp.exemplaire.livre.titre}'.\nRetard : {jours} jours.\nAmende actuelle : {emp.amende} DH.\nMerci de le rendre le plus tôt possible."
            
            self.envoyer_email(emp, subject, message)
            self.stdout.write(self.style.WARNING(f"Premier mail de retard envoyé à {emp.etudiant.user.email}"))

    def envoyer_email(self, emprunt, subject, message):
        try:
            send_mail(subject, message, 'admin@smartbiblio.com', [emprunt.etudiant.user.email])
            self.stdout.write(self.style.SUCCESS(f"Email envoyé à {emprunt.etudiant.user.email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur d'envoi : {e}"))