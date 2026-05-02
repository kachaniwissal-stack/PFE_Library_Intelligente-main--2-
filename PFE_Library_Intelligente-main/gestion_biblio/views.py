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
from django.contrib.auth.models import User 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- استيراد الموديلات والفورم ---
from .models import Livre, Emprunt, Etudiant, Exemplaire, Note, ListeAttente
from .forms import RegisterForm

# --- إعداد ذكاء Gemini ---
GOOGLE_API_KEY = "AIzaSy..." 
genai.configure(api_key=GOOGLE_API_KEY)
ai_model = genai.GenerativeModel('gemini-pro')

# 1. الدخول والخروج
class StudentLoginView(LoginView):
    template_name = 'gestion_biblio/login.html'
    def get_success_url(self): return '/mon-espace/'

def logout_user(request):
    logout(request)
    return redirect('home')

# دالة التسجيل
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 
            user.save()
            Etudiant.objects.create(user=user, cne=form.cleaned_data.get('cne'), niveau_etude=form.cleaned_data.get('niveau_etude'))
            try:
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
            except: return redirect('login')
    else: form = RegisterForm()
    return render(request, 'gestion_biblio/register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except: user = None
    if user is not None and (user.is_active or default_token_generator.check_token(user, token)):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('home')
    return render(request, 'gestion_biblio/activation_invalid.html')

# --- 2. فضاء الطالب (المعدلة لحساب التأخير والغرامات) ---
def mon_espace(request):
    if not request.user.is_authenticated: return redirect('login')
    try:
        etudiant = Etudiant.objects.get(user=request.user)
        historique = Emprunt.objects.filter(etudiant=etudiant).order_by('-date_emprunt')
        today = date.today()
        
        # متغيرات الحساب
        total_retards = 0
        total_amendes = 0

        for emp in historique:
            # تحديث حالة التأخير وحساب الغرامة
            if emp.statut != 'rendu' and emp.date_retour_prevue < today:
                days_late = (today - emp.date_retour_prevue).days
                emp.amende = days_late * 5 # 5 دراهم لليوم
                emp.statut = 'en retard'
                if not emp.alerte_envoyee:
                    try:
                        send_mail(f"🚨 RETARD : {emp.exemplaire.livre.titre}", f"Amende: {emp.amende} DH.", 'admin@smartbiblio.com', [request.user.email])
                        emp.alerte_envoyee = True
                    except: pass
                emp.save()

            # جمع الإحصائيات الفردية
            if emp.statut == 'en retard':
                total_retards += 1
                total_amendes += emp.amende

        return render(request, 'gestion_biblio/espace_etudiant.html', {
            'emprunts': historique,
            'total_retards': total_retards,
            'total_amendes': total_amendes
        })
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
    livres = Livre.objects.all()
    alternative_results, is_not_found = [], False
    if query:
        search_results = livres.filter(Q(titre__icontains=query) | Q(auteur__icontains=query))
        if search_results.exists(): livres = search_results
        else:
            is_not_found, livres = True, []
            alternative_results = get_smart_recommendations(request.user)[:3]
    for livre in (alternative_results if is_not_found else livres):
        livre.disponible = livre.exemplaires.filter(est_disponible=True).exists()
    recommandations = get_smart_recommendations(request.user) if request.user.is_authenticated else Livre.objects.all().order_by('?')[:4]
    for r in recommandations: r.disponible = r.exemplaires.filter(est_disponible=True).exists()
    return render(request, 'gestion_biblio/index.html', {'livres': livres, 'recommandations': recommandations, 'query': query, 'is_not_found': is_not_found, 'alternative_results': alternative_results})

# 4. الشات بوت
@csrf_exempt
def chatbot_response(request):
    import json
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            msg = data.get('message', '').strip().lower()
            if any(word in msg for word in ["salut", "bonjour"]): reply = "Bonjour ! 😊 Comment puis-je vous aider ?"
            elif "livre" in msg: reply = "Vous pouvez chercher des livres dans la barre de recherche ! 📚"
            elif "retard" in msg or "amende" in msg: reply = "L'amende est de 5 DH par jour. Vérifiez 'Mon Espace'."
            else: reply = "Je suis là pour vous aider avec les réservations."
            return JsonResponse({'reply': reply})
        except: return JsonResponse({'reply': "Désolé, erreur technique."})
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
        messages.success(request, "Votre livre a été réservé ! 📚")
    return redirect('mon_espace')

def annuler_reservation(request, emprunt_id):
    emp = get_object_or_404(Emprunt, id=emprunt_id, etudiant__user=request.user)
    if emp.statut != 'rendu':
        ex = emp.exemplaire
        ex.est_disponible = True
        ex.save()
        emp.delete()
        messages.success(request, "Votre réservation a été annulée. ✅")
    return redirect('mon_espace')

# 6. باقي الدوال
def detail_livre(request, id):
    livre = get_object_or_404(Livre, id=id)
    dispo = livre.exemplaires.filter(est_disponible=True).exists()
    return render(request, 'gestion_biblio/detail.html', {'livre': livre, 'disponible': dispo})

def dashboard(request):
    import json
    stats = Livre.objects.values('categorie').annotate(total_cat=Count('id'))
    labels_list = [str(s['categorie']) for s in stats]
    data_list = [int(s['total_cat']) for s in stats]
    return render(request, 'gestion_biblio/dashboard.html', {
        'total': Livre.objects.count(),
        'disponibles': Exemplaire.objects.filter(est_disponible=True).count(),
        'empruntes': Emprunt.objects.filter(statut='en cours').count(),
        'labels_js': json.dumps(labels_list),
        'data_js': json.dumps(data_list),
    })

def ajouter_note(request, id):
    if request.method == "POST": 
        Note.objects.create(livre=get_object_or_404(Livre, id=id), etudiant=Etudiant.objects.get(user=request.user), valeur=request.POST.get('valeur'))
        messages.success(request, "Votre note a été enregistrée ! ⭐")
    return redirect('detail_livre', id=id)

def rejoindre_attente(request, livre_id):
    if not request.user.is_authenticated: return redirect('register')
    livre = get_object_or_404(Livre, id=livre_id)
    etudiant = Etudiant.objects.get(user=request.user)
    ListeAttente.objects.get_or_create(livre=livre, etudiant=etudiant)
    messages.success(request, "Vous avez été ajouté à la liste d'attente ! 📧")
    return redirect('detail_livre', id=livre_id)