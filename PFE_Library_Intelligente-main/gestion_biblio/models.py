from django.db import models
from django.contrib.auth.models import User

class Livre(models.Model):
    titre = models.CharField(max_length=200)
    auteur = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True)
    categorie = models.CharField(max_length=100) # HADI LI KANT KHASSAK
    est_disponible = models.BooleanField(default=True)
    image = models.ImageField(upload_to='couvertures/', blank=True, null=True)
    image = models.ImageField(upload_to='couvertures/', blank=True, null=True)
    def __str__(self):
        return self.titre
   
    
   

class Etudiant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cne = models.CharField(max_length=20)
    niveau_etude = models.CharField(max_length=50)

    def __str__(self):
        return self.user.username

class Emprunt(models.Model):
    STATUT_CHOICES = [
        ('en cours', 'En cours'),
        ('rendu', 'Rendu'),
        ('en retard', 'En retard'),
    ]
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE)
    date_emprunt = models.DateField(auto_now_add=True)
    date_retour_prevue = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en cours')

    def __str__(self):
        return f"{self.etudiant.user.username} - {self.livre.titre}"