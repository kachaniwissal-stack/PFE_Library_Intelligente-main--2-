from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from gestion_biblio.models import Emprunt

class Command(BaseCommand):
    help = 'Gère les rappels de délai et les alertes de retard'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(f"Vérification du : {today}")

        # --- 1. تذكير بآخر أجل (اليوم) ---
        rappels = Emprunt.objects.filter(date_retour_prevue=today, statut='en cours', alerte_envoyee=False)
        for emp in rappels:
            self.envoyer_email(
                emp.etudiant.user.email,
                "⏳ Rappel : Dernier délai aujourd'hui",
                f"Bonjour {emp.etudiant.user.first_name},\n\nC'est aujourd'hui le dernier délai pour rendre '{emp.exemplaire.livre.titre}'.\nMerci de le retourner dès que possible.\n\nCordialement,\nL'équipe Smart-Biblio 📚"
            )
            emp.alerte_envoyee = True
            emp.save()

        # --- 2. إنذار التأخير (كل 24h) ---
        retards = Emprunt.objects.filter(
            date_retour_prevue__lt=today,
            statut__in=['en cours', 'en retard']
        )

        for emp in retards:
            diff = today - emp.date_retour_prevue
            jours = diff.days
            emp.amende = jours * 5
            emp.statut = 'en retard'
            emp.save()

            self.envoyer_email(
                emp.etudiant.user.email,
                f"🚨 ALERTE RETARD : {emp.exemplaire.livre.titre}",
                f"Bonjour {emp.etudiant.user.first_name},\n\nVous avez dépassé le délai pour le livre '{emp.exemplaire.livre.titre}'.\nRetard : {jours} jours.\nAmende actuelle : {emp.amende} DH.\nMerci de le rendre le plus tôt possible.\n\nCordialement,\nL'équipe Smart-Biblio 📚"
            )
            self.stdout.write(self.style.WARNING(f"Mail retard envoyé à {emp.etudiant.user.email}"))

    def envoyer_email(self, email, subject, message):
        try:
            send_mail(subject, message, 'admin@smartbiblio.com', [email])
            self.stdout.write(self.style.SUCCESS(f"Email envoyé à {email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur d'envoi : {e}"))