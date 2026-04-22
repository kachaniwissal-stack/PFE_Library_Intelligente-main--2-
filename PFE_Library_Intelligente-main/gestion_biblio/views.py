from django.shortcuts import render, get_object_or_404, redirect
from .models import Livre, Emprunt, Etudiant, Exemplaire
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib import messages
from django.http import JsonResponse
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import date

# 1. نظام التوصية المطور (IA)
def get_smart_recommendations(user):
    livres = Livre.objects.all()
    if livres.count() < 2: return list(livres)
    df = pd.DataFrame(list(livres.values('id', 'titre', 'description', 'categorie')))
    df['metadata'] = df['description'].fillna('') + " " + df['categorie']
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['metadata'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    try:
        dernier = Emprunt.objects.filter(etudiant__user=user).latest('date_emprunt')
        idx = df[df['id'] == dernier.exemplaire.livre.id].index[0]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:5]
        return Livre.objects.filter(id__in=df.iloc[[i[0] for i in sim_scores]]['id'].values)
    except:
        return Livre.objects.all().order_by('?')[:4]

# 2. الصفحة الرئيسية
def home(request):
    query = request.GET.get('q')
    tous_les_livres = Livre.objects.all()
    if query:
        tous_les_livres = tous_les_livres.filter(Q(titre__icontains=query) | Q(auteur__icontains=query))
    
    recommandations = get_smart_recommendations(request.user) if request.user.is_authenticated else Livre.objects.all()[:4]
    
    for l in tous_les_livres: l.disponible = l.exemplaires.filter(est_disponible=True).exists()
    for r in recommandations: r.disponible = r.exemplaires.filter(est_disponible=True).exists()

    return render(request, 'gestion_biblio/index.html', {'livres': tous_les_livres, 'recommandations': recommandations})

# 3. فضاء الطالب + حساب الغرامات تلقائياً (Logic Rapport p.7)
def mon_espace(request):
    if request.user.is_authenticated:
        etudiant = Etudiant.objects.get(user=request.user)
        historique = Emprunt.objects.filter(etudiant=etudiant).order_by('-date_emprunt')
        today = date.today()

        for emp in historique:
            if emp.statut == 'en cours' and emp.date_retour_prevue < today:
                emp.amende = (today - emp.date_retour_prevue).days * 5
                emp.statut = 'en retard'
                
                # --- اللعبية الجديدة: صيفط إيميل ---
                if not emp.alerte_envoyee:
                    subject = f"Retard de retour : {emp.exemplaire.livre.titre}"
                    message = f"Bonjour {request.user.username},\n\nLe livre '{emp.exemplaire.livre.titre}' est en retard. Une amende de {emp.amende} DH a été appliquée.\nMerci de le rendre rapidement.\n\nL'équipe Smart-Biblio."
                    
                    try:
                        send_mail(subject, message, 'admin@smartbiblio.com', [request.user.email])
                        emp.alerte_envoyee = True # باش ما يعاودش يصيفط ليه
                    except:
                        pass # إلا مكانش كونيكسيون ما يتبلوكاش السيت
                
                emp.save()

        return render(request, 'gestion_biblio/espace_etudiant.html', {'emprunts': historique})
    return redirect('admin:login')

# 4. باقي الدوال
def dashboard(request):
    stats = Livre.objects.values('categorie').annotate(total_cat=Count('id'))
    return render(request, 'gestion_biblio/dashboard.html', {
        'total': Livre.objects.count(), 
        'disponibles': Exemplaire.objects.filter(est_disponible=True).count(),
        'empruntes': Emprunt.objects.filter(statut='en cours').count(),
        'stats': stats
    })

def chatbot_response(request):
    msg = request.GET.get('message', '').lower()
    res = "Je suis l'IA de Smart-Biblio. Réalisé par Wissal et Ilham."
    if "ia" in msg: res = "J'utilise TF-IDF et Scikit-learn pour les recommandations."
    elif "créateur" in msg: res = "Ce site a été conçu par Wissal et Ilham."
    return JsonResponse({'response': res})

def reserver_livre(request, id):
    livre = get_object_or_404(Livre, id=id)
    exemplaire = Exemplaire.objects.filter(livre=livre, est_disponible=True).first()
    if exemplaire and request.user.is_authenticated:
        exemplaire.est_disponible = False
        exemplaire.save()
        Emprunt.objects.create(etudiant=Etudiant.objects.get(user=request.user), exemplaire=exemplaire, date_retour_prevue=timezone.now().date() + timezone.timedelta(days=15))
        messages.success(request, "Livre réservé !")
    return redirect('mon_espace')

def detail_livre(request, id):
    return render(request, 'gestion_biblio/detail.html', {'livre': get_object_or_404(Livre, id=id)})