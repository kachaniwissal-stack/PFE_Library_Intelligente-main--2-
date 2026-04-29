import json
import pandas as pd
import google.generativeai as genai
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.csrf import csrf_exempt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- استيراد الموديلات والفورم ---
from .models import Livre, Emprunt, Etudiant, Exemplaire, Note, ListeAttente
from .forms import RegisterForm

# --- إعداد ذكاء Gemini (تأكدي من الـ API Key) ---
GOOGLE_API_KEY = "AIzaSy..."  # <--- حطي الكود ديالك هنا
genai.configure(api_key=GOOGLE_API_KEY)
# استعملنا gemini-pro حيت هو اللي خدام مزيان مع v1beta
ai_model = genai.GenerativeModel('gemini-pro')

# 1. الدخول والخروج والتسجيل
class StudentLoginView(LoginView):
    template_name = 'gestion_biblio/login.html'
    def get_success_url(self): return '/mon-espace/'

def logout_user(request):
    logout(request)
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 
            user.save()
            Etudiant.objects.create(user=user, cne=form.cleaned_data.get('cne'), niveau_etude=form.cleaned_data.get('niveau_etude'))
            current_site = get_current_site(request)
            mail_subject = 'Activez votre compte Smart-Biblio 📚'
            message = render_to_string('gestion_biblio/acc_active_email.html', {
                'user': user, 'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()
            return render(request, 'gestion_biblio/check_email.html')
    else: form = RegisterForm()
    return render(request, 'gestion_biblio/register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        from django.contrib.auth.models import User
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except: user = None
    if user is not None and user.is_active:
        login(request, user)
        return redirect('home')
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, "Compte activé ! 😊")
        return redirect('home')
    return render(request, 'gestion_biblio/activation_invalid.html')

# 2. فضاء الطالب
def mon_espace(request):
    if not request.user.is_authenticated: return redirect('login')
    try:
        etudiant = Etudiant.objects.get(user=request.user)
        historique = Emprunt.objects.filter(etudiant=etudiant).order_by('-date_emprunt')
        today = date.today()
        for emp in historique:
            if emp.statut == 'en cours' and emp.date_retour_prevue < today:
                emp.amende = (today - emp.date_retour_prevue).days * 5
                emp.statut = 'en retard'
                if not emp.alerte_envoyee:
                    try:
                        send_mail(f"🚨 RETARD : {emp.exemplaire.livre.titre}", f"Bonjour, amende : {emp.amende} DH.", 'admin@smartbiblio.com', [request.user.email])
                        emp.alerte_envoyee = True
                    except: pass
                emp.save()
        return render(request, 'gestion_biblio/espace_etudiant.html', {'emprunts': historique})
    except: return redirect('register')

# 3. نظام التوصية والبحث
def get_smart_recommendations(user):
    livres = Livre.objects.all()
    if livres.count() < 2: return list(livres)
    df = pd.DataFrame(list(livres.values('id', 'description', 'categorie')))
    df['meta'] = (df['categorie'] + " ") * 3 + df['description'].fillna('')
    tfidf = TfidfVectorizer().fit_transform(df['meta'])
    try:
        dernier = Emprunt.objects.filter(etudiant__user=user).latest('date_emprunt')
        idx = df[df['id'] == dernier.exemplaire.livre.id].index[0]
        sim = cosine_similarity(tfidf, tfidf)[idx]
        indices = sorted(list(enumerate(sim)), key=lambda x: x[1], reverse=True)[1:5]
        return Livre.objects.filter(id__in=[df.iloc[i[0]]['id'] for i in indices])
    except: return Livre.objects.all().order_by('?')[:4]

def home(request):
    query = request.GET.get('q')
    tous_les_livres = Livre.objects.all()
    alternative_results, is_not_found = [], False

    if query:
        search_results = tous_les_livres.filter(Q(titre__icontains=query) | Q(auteur__icontains=query))
        if search_results.exists():
            tous_les_livres = search_results
        else:
            is_not_found = True
            tous_les_livres = []
            alternative_results = get_smart_recommendations(request.user)[:3]

    # --- تصحيح مشكلة "Reserved" ---
    # كنأكدوا لكل كتاب واش كاين شي نسخة ديالو موجودة بصح
    livres_a_afficher = alternative_results if is_not_found else tous_les_livres
    for livre in livres_a_afficher:
        livre.disponible = livre.exemplaires.filter(est_disponible=True).exists()

    recommandations = get_smart_recommendations(request.user) if request.user.is_authenticated else Livre.objects.all().order_by('?')[:4]
    for r in recommandations:
        r.disponible = r.exemplaires.filter(est_disponible=True).exists()

    return render(request, 'gestion_biblio/index.html', {
        'livres': tous_les_livres, 
        'recommandations': recommandations, 
        'query': query, 
        'is_not_found': is_not_found, 
        'alternative_results': alternative_results
    })

# 4. الشات بوت الذكي (Gemini AI)
@csrf_exempt
def chatbot_response(request):
    import json
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            msg = data.get('message', '').strip().lower()
            
            # --- 1. الترحيب ---
            if any(word in msg for word in ["salut", "bonjour", "hi", "hello"]):
                reply = "Bonjour ! 😊 Je suis l'assistant Smart-Biblio. Comment puis-je vous aider aujourd'hui ?"
            
            # --- 2. البحث عن الكتب (بشكل عام) ---
            elif any(word in msg for word in ["livre", "chercher", "trouver", "book"]):
                reply = "Vous pouvez rechercher n'importe quel livre en utilisant la barre de recherche en haut de la page d'accueil ! 📚"
            
            # --- 3. معلومات عن التوافر (Disponibilité) ---
            elif any(word in msg for word in ["disponible", "stock", "existe"]):
                reply = "La disponibilité est indiquée à côté de chaque livre (✅ Disponible ou ❌ Emprunté). Vous pouvez aussi réserver ceux qui sont libres."
            
            # --- 4. معلومات عن التأخير والغرامات ---
            elif any(word in msg for word in ["retard", "amende", "dh", "argent"]):
                reply = "En cas de retard, une amende de 5 DH par jour est appliquée. Vous pouvez voir vos retards dans votre espace personnel."
            
            # --- 5. معلومات عن البروجي (PFE) ---
            elif any(word in msg for word in ["pfe", "projet", "qui es-tu", "fsbm"]):
                reply = "Je suis Smart-Biblio AI, un projet de bibliothèque intelligente conçu pour les étudiants de la FSBM. 🎓"

            # --- 6. الشكر ---
            elif any(word in msg for word in ["merci", "shokran", "thanks"]):
                reply = "Je vous en prie ! N'hésitez pas si vous avez d'autres questions. 😊"

            # --- 7. جواب افتراضي إذا لم يفهم ---
            else:
                reply = "C'est une excellente question ! 🧐 Pourriez-vous être plus précis ? Vous pouvez me poser des questions sur les livres, les amendes ou le fonctionnement de la bibliothèque."

            return JsonResponse({'reply': reply})
            
        except Exception as e:
            return JsonResponse({'reply': "Désolé, je rencontre une petite erreur technique."})
            
    return JsonResponse({'reply': 'Erreur'})

# 5. دوال الحجز والإلغاء
def reserver_livre(request, id):
    if not request.user.is_authenticated: return redirect('register')
    etudiant = Etudiant.objects.get(user=request.user)
    livre = get_object_or_404(Livre, id=id)
    ex = Exemplaire.objects.filter(livre=livre, est_disponible=True).first()
    if ex:
        ex.est_disponible = False
        ex.save()
        Emprunt.objects.create(etudiant=etudiant, exemplaire=ex, date_retour_prevue=date.today() + timezone.timedelta(days=15))
        messages.success(request, "Réservation réussie ! ✅")
    return redirect('mon_espace')

def annuler_reservation(request, emprunt_id):
    emp = get_object_or_404(Emprunt, id=emprunt_id, etudiant__user=request.user)
    if emp.statut != 'rendu':
        exemplaire = emp.exemplaire
        exemplaire.est_disponible = True
        exemplaire.save()
        emp.delete()
        messages.success(request, "Réservation annulée. ✅")
    return redirect('mon_espace')

# 6. باقي الدوال
def detail_livre(request, id):
    livre = get_object_or_404(Livre, id=id)
    dispo = livre.exemplaires.filter(est_disponible=True).exists()
    return render(request, 'gestion_biblio/detail.html', {'livre': livre, 'disponible': dispo})

def dashboard(request):
    return render(request, 'gestion_biblio/dashboard.html', {
        'total': Livre.objects.count(), 
        'disponibles': Exemplaire.objects.filter(est_disponible=True).count(),
        'empruntes': Emprunt.objects.filter(statut='en cours').count()
    })

def ajouter_note(request, id):
    if request.method == "POST": 
        Note.objects.create(livre=get_object_or_404(Livre, id=id), etudiant=Etudiant.objects.get(user=request.user), valeur=request.POST.get('valeur'))
    return redirect('detail_livre', id=id)

def rejoindre_attente(request, livre_id):
    if not request.user.is_authenticated: return redirect('register')
    livre = get_object_or_404(Livre, id=livre_id)
    etudiant = Etudiant.objects.get(user=request.user)
    ListeAttente.objects.get_or_create(livre=livre, etudiant=etudiant)
    messages.success(request, "Inscrit sur la liste d'attente ! 📧")
    return redirect('detail_livre', id=livre_id)