import os
import django

# إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibliotheque_project.settings')
django.setup()

from gestion_biblio.models import Exemplaire

def run_fix():
    try:
        # هادا هو السطر السحري لي كيرد كولشي أخضر
        count = Exemplaire.objects.all().update(est_disponible=True)
        print(f"✅ Succès ! {count} exemplaires sont maintenant Disponibles.")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    run_fix()