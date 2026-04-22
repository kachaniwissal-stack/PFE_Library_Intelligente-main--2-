import os
import django
import json

# هاد السطور كيعلمو البوت بلي حنا فمشروع Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibliotheque_project.settings')
django.setup()

from gestion_biblio.models import Livre, Exemplaire

def run():
    try:
        with open('livres.json', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data:
                fields = entry['fields']
                # 1. كنكريو الكتاب
                l, created = Livre.objects.get_or_create(
                    titre=fields['titre'],
                    auteur=fields['auteur'],
                    isbn=fields.get('isbn', '0000'),
                    categorie=fields['categorie']
                )
                # 2. كنكريو النسخة (Exemplaire) لي زدنا فـ UML
                Exemplaire.objects.get_or_create(
                    livre=l,
                    id_exemplaire=f"EXP-{l.id}",
                    defaults={'est_disponible': True}
                )
        print("✅ Success: Tous les livres ont été importés !")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    run()