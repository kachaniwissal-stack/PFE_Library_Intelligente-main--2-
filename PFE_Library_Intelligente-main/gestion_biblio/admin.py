from django.contrib import admin
from .models import Etudiant, Livre, Exemplaire, Emprunt

admin.site.register(Etudiant)
admin.site.register(Livre)
admin.site.register(Exemplaire)
admin.site.register(Emprunt)