from django.db import models
from django.contrib.auth.models import User

class Etudiant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cne = models.CharField(max_length=20)
    niveau_etude = models.CharField(max_length=50)
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
    etat = models.CharField(max_length=50, default="Bon")
    est_disponible = models.BooleanField(default=True)
    def __str__(self): return f"{self.livre.titre} ({self.id_exemplaire})"

class Emprunt(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    exemplaire = models.ForeignKey(Exemplaire, on_delete=models.CASCADE)
    date_emprunt = models.DateField(auto_now_add=True)
    date_retour_prevue = models.DateField()
    statut = models.CharField(max_length=20, default="en cours")
    amende = models.IntegerField(default=0) # السطر الجديد لي فـ Rapport
    alerte_envoyee = models.BooleanField(default=False)
    def __str__(self): return f"{self.etudiant.user.username} - {self.exemplaire.livre.titre}"