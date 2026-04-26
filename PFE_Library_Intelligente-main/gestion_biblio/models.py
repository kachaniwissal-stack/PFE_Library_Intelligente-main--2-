from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

class Etudiant(models.Model):
    NIVEAU_CHOICES = [
        ('', '--- Choisir ---'), ('L1-MIP', 'L1 (MIP)'), ('L1-SPC', 'L1 (SPC)'), ('L1-BCG', 'L1 (BCG)'),
        ('L2-MIP', 'L2 (MIP)'), ('L2-SPC', 'L2 (SPC)'), ('L2-BCG', 'L2 (BCG)'),
        ('L3-Info', 'L3 Info'), ('M1', 'Master 1'), ('M2', 'Master 2'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cne = models.CharField(max_length=20)
    niveau_etude = models.CharField(max_length=50, choices=NIVEAU_CHOICES)
    def __str__(self): return self.user.username

class Livre(models.Model):
    titre = models.CharField(max_length=200)
    auteur = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20)
    categorie = models.CharField(max_length=100)
    image = models.ImageField(upload_to='couvertures/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    def __str__(self): return self.titre

class Exemplaire(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name="exemplaires")
    id_exemplaire = models.CharField(max_length=50, unique=True)
    est_disponible = models.BooleanField(default=True)
    def __str__(self): return f"{self.livre.titre} ({self.id_exemplaire})"

class Emprunt(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    exemplaire = models.ForeignKey(Exemplaire, on_delete=models.CASCADE)
    date_emprunt = models.DateField(auto_now_add=True)
    date_retour_prevue = models.DateField()
    statut = models.CharField(max_length=20, default="en cours")
    amende = models.IntegerField(default=0)
    alerte_envoyee = models.BooleanField(default=False)
    rappel_envoye = models.BooleanField(default=False)

class Note(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name="notes")
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    valeur = models.IntegerField(default=5)

class ListeAttente(models.Model):
     livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name="attente")
     etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
     date_demande = models.DateTimeField(auto_now_add=True)
     def __str__(self):
        return f"{self.etudiant.user.username} attend {self.livre.titre}"

# --- هاد الجزء هو اللي كيدير "الفاكتور" (صيفط الإيميل أوتوماتيكيا) ---

@receiver(post_save, sender=Exemplaire)
def notifier_liste_attente(sender, instance, **kwargs):
    # كنشوفو واش الكتاب ولّا متاح (est_disponible = True)
    if instance.est_disponible:
        # كنجبدو الطلبة اللي كيتسناو هاد الكتاب بالضبط
        attentes = ListeAttente.objects.filter(livre=instance.livre)
        
        for attente in attentes:
            subject = f"📚 Bonne nouvelle : {instance.livre.titre} est disponible !"
            message = f"Bonjour {attente.etudiant.user.username},\n\nLe livre '{instance.livre.titre}' que vous attendiez est de nouveau disponible. Réservez-le vite sur Smart-Biblio !\n\nL'équipe Smart-Biblio."
            
            # صيفط الإيميل
            send_mail(
                subject,
                message,
                'noreply@smartbiblio.com', # إيميل المرسل
                [attente.etudiant.user.email], # إيميل الطالب
                fail_silently=True,
            )
            # مسحو من اللائحة حيت صافي علمناه
            attente.delete()