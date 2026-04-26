from django.shortcuts import render, get_object_or_404, redirect
from .models import Livre, Emprunt, Etudiant, Exemplaire, Note, ListeAttente
from .forms import RegisterForm
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from datetime import date
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

# 1. الدخول والخروج والتسجيل مع التفعيل
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
            
            # إرسال إيميل التفعيل
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
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except: user = None

    # اللعبة هنا: إلا كان ديجا Active، دخلو نيشان بلا ما توري ليه "Invalide"
    if user is not None and user.is_active:
        login(request, user)
        messages.info(request, "Votre compte est déjà activé. Bienvenue !")
        return redirect('home')

    # تفعيل الحساب لأول مرة
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, "Félicitations ! Votre compte est activé. 😊")
        return redirect('home')
    else:
        return render(request, 'gestion_biblio/activation_invalid.html')

# 2. فضاء الطالب + نظام التذكيرات الأوتوماتيكي (Gmail)
def mon_espace(request):
    if not request.user.is_authenticated: return redirect('login')
    try:
        etudiant = Etudiant.objects.get(user=request.user)
        historique = Emprunt.objects.filter(etudiant=etudiant).order_by('-date_emprunt')
        today = date.today()

        for emp in historique:
            # --- أ: تذكير يوم الإرجاع (Rappel Préventif) ---
            if emp.statut == 'en cours' and emp.date_retour_prevue == today:
                if not emp.rappel_envoye:
                    subject = f"⚠️ RAPPEL : Retour de livre aujourd'hui"
                    msg = f"Bonjour {request.user.username},\n\nC'est aujourd'hui le dernier délai pour rendre '{emp.exemplaire.livre.titre}'.\n\nL'équipe Smart-Biblio."
                    send_mail(subject, msg, 'notif@smartbiblio.com', [request.user.email])
                    emp.rappel_envoye = True
                    emp.save()

            # --- ب: تنبيه التأخير (Alerte Retard) ---
            elif emp.statut == 'en cours' and emp.date_retour_prevue < today:
                jours = (today - emp.date_retour_prevue).days
                emp.amende = jours * 5
                emp.statut = 'en retard'
                if not emp.alerte_envoyee:
                    subject = f"🚨 RETARD : Amende de {emp.amende} DH"
                    msg = f"Bonjour {request.user.username},\n\nLe livre '{emp.exemplaire.livre.titre}' est en retard de {jours} jours. Merci de le rendre rapidement."
                    send_mail(subject, msg, 'admin@smartbiblio.com', [request.user.email])
                    emp.alerte_envoyee = True
                emp.save()

        return render(request, 'gestion_biblio/espace_etudiant.html', {'emprunts': historique})
    except: return redirect('register')

# 3. نظام التوصية والبحث (IA)
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
    tous = Livre.objects.all()
    alt, not_found = [], False
    if query:
        res = tous.filter(Q(titre__icontains=query) | Q(auteur__icontains=query))
        if res.exists(): tous = res
        else:
            not_found, tous = True, []
            alt = Livre.objects.all().order_by('?')[:3]
    recom = get_smart_recommendations(request.user) if request.user.is_authenticated else tous[:4]
    for l in (tous or alt): l.disponible = l.exemplaires.filter(est_disponible=True).exists()
    return render(request, 'gestion_biblio/index.html', {'livres': tous, 'recommandations': recom, 'query': query, 'alternative_results': alt, 'is_not_found': not_found})

# 4. باقي الدوال (تفاصيل، حجز، بوت، داشبورد)
def detail_livre(request, id):
    livre = get_object_or_404(Livre, id=id)
    moy = livre.notes.aggregate(Avg('valeur'))['valeur__avg'] or 5.0
    sim = Livre.objects.filter(categorie=livre.categorie).exclude(id=id)[:3]
    dispo = livre.exemplaires.filter(est_disponible=True).exists()
    return render(request, 'gestion_biblio/detail.html', {'livre': livre, 'moyenne': round(float(moy), 1), 'similaires': sim, 'disponible': dispo})

# 1. حجز كتاب (مع قانون: كتاب واحد فقط)
def reserver_livre(request, id):
    if not request.user.is_authenticated: return redirect('register')
    
    etudiant = Etudiant.objects.get(user=request.user)
    
    # --- اللعبة الذكية: واش عندو شي كتاب ديجا؟ ---
    deja_un_livre = Emprunt.objects.filter(etudiant=etudiant, statut__in=['en cours', 'en retard']).exists()
    
    if deja_un_livre:
        messages.error(request, "Désolé ! Vous ne pouvez réserver qu'un seul livre à la fois. Veuillez rendre votre livre actuel d'abord. 📚")
        return redirect('mon_espace')

    livre = get_object_or_404(Livre, id=id)
    ex = Exemplaire.objects.filter(livre=livre, est_disponible=True).first()
    
    if ex:
        ex.est_disponible = False
        ex.save()
        Emprunt.objects.create(
            etudiant=etudiant, 
            exemplaire=ex, 
            date_retour_prevue=date.today() + timezone.timedelta(days=15)
        )
        messages.success(request, f"Le livre '{livre.titre}' a été réservé ! Allez le chercher à la bibliothèque. 🏃‍♂️")
    return redirect('mon_espace')

# 2. إلغاء الحجز (Annuler)
def annuler_reservation(request, emprunt_id):
    emp = get_object_or_404(Emprunt, id=emprunt_id, etudiant__user=request.user)
    
    # كنقدرو نلغيو غير إلا كان "en cours" وباقي ما ولّاش "retard"
    if emp.statut == 'en cours':
        ex = emp.exemplaire
        ex.est_disponible = True # الكتاب يرجع للمخزن
        ex.save()
        emp.delete() # نمسحو طلب الاستعارة
        messages.success(request, "Réservation annulée. Le livre est de nouveau disponible pour les autres. ✅")
    
    return redirect('mon_espace')

def dashboard(request):
    return render(request, 'gestion_biblio/dashboard.html', {'total': Livre.objects.count(), 'disponibles': Exemplaire.objects.filter(est_disponible=True).count(), 'empruntes': Emprunt.objects.filter(statut='en cours').count(), 'stats': Livre.objects.values('categorie').annotate(total_cat=Count('id'))})

def chatbot_response(request):
    msg = request.GET.get('message', '').lower()
    return JsonResponse({'response': "Bonjour ! Je suis l'IA de Smart-Biblio. Posez-moi une question !"})

def ajouter_note(request, id):
    if request.method == "POST" and request.user.is_authenticated:
        Note.objects.create(livre=get_object_or_404(Livre, id=id), etudiant=Etudiant.objects.get(user=request.user), valeur=request.POST.get('valeur'))
    return redirect('detail_livre', id=id)

def rejoindre_attente(request, livre_id):
    if not request.user.is_authenticated: 
        return redirect('register')
    
    livre = get_object_or_404(Livre, id=livre_id)
    etudiant = get_object_or_404(Etudiant, user=request.user)
    
    # واش الطالب ديجا كاين فاللائحة باش ما يتعاودش؟
    deja_inscrit = ListeAttente.objects.filter(livre=livre, etudiant=etudiant).exists()
    
    if not deja_inscrit:
        ListeAttente.objects.create(livre=livre, etudiant=etudiant)
        messages.success(request, "C'est fait ! Vous recevrez un email dès que ce livre sera disponible. 📧")
    else:
        messages.info(request, "Vous êtes déjà inscrit dans la liste d'attente pour ce livre.")
    
    # التصحيح المهم هنا: استعملنا id=livre_id عوض livre_id=livre_id
    return redirect('detail_livre', id=livre_id)