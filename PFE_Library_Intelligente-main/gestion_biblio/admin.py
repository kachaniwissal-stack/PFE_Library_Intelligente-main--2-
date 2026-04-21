from django.contrib import admin
from .models import Livre, Etudiant, Emprunt

admin.site.register(Livre)
admin.site.register(Etudiant)
admin.site.register(Emprunt)