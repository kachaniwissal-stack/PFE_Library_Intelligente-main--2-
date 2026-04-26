from django.contrib import admin
from .models import Etudiant, Livre, Exemplaire, Emprunt, Note, ListeAttente

# تخصيص واجهة الكتاب باش تبين عدد النسخ
class LivreAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'categorie', 'nombre_exemplaires')

    def nombre_exemplaires(self, obj):
        # كيحسب شحال من نسخة كاينا لهاد الكتاب
        return obj.exemplaires.count()
    
    nombre_exemplaires.short_description = "Nb Exemplaires"

admin.site.register(Livre, LivreAdmin) # سجلناه بـ التخصيص الجديد
admin.site.register(Exemplaire)
admin.site.register(Etudiant)
admin.site.register(Emprunt)
admin.site.register(Note)
admin.site.register(ListeAttente)