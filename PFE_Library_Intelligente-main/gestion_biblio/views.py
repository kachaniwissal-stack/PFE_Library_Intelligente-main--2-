from django.shortcuts import render, get_object_or_404, redirect
from .models import Livre, Emprunt, Etudiant
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages

# 1. الصفحة الرئيسية (البحث + التوصيات الذكية)
def home(request):
    query = request.GET.get('q')
    if query:
        tous_les_livres = Livre.objects.filter(
            Q(titre__icontains=query) | Q(auteur__icontains=query)
        )
    else:
        tous_les_livres = Livre.objects.all()

    recommandations = []
    if request.user.is_authenticated:
        try:
            dernier_emprunt = Emprunt.objects.filter(etudiant__user=request.user).latest('date_emprunt')
            recommandations = Livre.objects.filter(categorie=dernier_emprunt.livre.categorie).exclude(id=dernier_emprunt.livre.id)[:4]
        except:
            recommandations = Livre.objects.all().order_by('?')[:4]
    else:
        recommandations = Livre.objects.all().order_by('-id')[:4]

    return render(request, 'gestion_biblio/index.html', {
        'livres': tous_les_livres,
        'recommandations': recommandations,
        'query': query,
    })

# 2. تفاصيل الكتاب
def detail_livre(request, id):
    livre = get_object_or_404(Livre, id=id)
    return render(request, 'gestion_biblio/detail.html', {'livre': livre})

# 3. فضاء الطالب
def mon_espace(request):
    if request.user.is_authenticated:
        mes_emprunts = Emprunt.objects.filter(etudiant__user=request.user)
        return render(request, 'gestion_biblio/espace_etudiant.html', {'emprunts': mes_emprunts})
    return redirect('admin:login')

# 4. حساب التأخير (هادي زدتها باش ما يوقعش Error)
def calculer_retards(request):
    today = timezone.now().date()
    emprunts_en_retard = Emprunt.objects.filter(date_retour_prevue__lt=today, statut='en cours')
    for emprunt in emprunts_en_retard:
        emprunt.statut = 'en retard'
        emprunt.save()
    return render(request, 'gestion_biblio/retards.html', {'count': emprunts_en_retard.count()})

# 5. حجز كتاب
def reserver_livre(request, id):
    livre = get_object_or_404(Livre, id=id)
    if not request.user.is_authenticated:
        return redirect('admin:login')

    if livre.est_disponible:
        livre.est_disponible = False
        livre.save()
        try:
            etudiant = Etudiant.objects.get(user=request.user)
            Emprunt.objects.create(
                etudiant=etudiant,
                livre=livre,
                date_retour_prevue=timezone.now().date() + timezone.timedelta(days=15),
                statut='en cours'
            )
            messages.success(request, f"Le livre '{livre.titre}' a été réservé !")
        except Etudiant.DoesNotExist:
            messages.error(request, "Erreur: Profil étudiant introuvable.")
            
    return redirect('mon_espace')