import json
import pandas as pd
import requests
import time
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User 
from django.contrib.admin.views.decorators import staff_member_required
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
 
from .models import Livre, Emprunt, Etudiant, Exemplaire, Note, ListeAttente
from .forms import RegisterForm
from groq import Groq
 
client = Groq(api_key="")
 
 
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
            
            Etudiant.objects.create(
                user=user, 
                cne=form.cleaned_data.get('cne'), 
                niveau_etude=form.cleaned_data.get('niveau_etude')
            )
 
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
            except Exception as e:
                return redirect('login') 
    else:
        form = RegisterForm()
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
 
# --- 2. فضاء الطالب ---
def mon_espace(request):
    if not request.user.is_authenticated: return redirect('login')

    try:
        etudiant = Etudiant.objects.get(user=request.user)
        historique = Emprunt.objects.filter(etudiant=etudiant, statut__in=['en cours', 'en retard']).order_by('-date_emprunt')
        today = date.today()

        for emp in historique:
            # --- تأكيد التذكير ديال اليوم أ وصال ---
            if emp.date_retour_prevue == today:
                if not emp.rappel_envoye:
                    subject = f"⚠️ DERNIER DÉLAI : {emp.exemplaire.livre.titre}"
                    msg = f"Bonjour {request.user.username}, c'est aujourd'hui le dernier délai pour rendre votre livre. Évitez les amendes ! 😊"
                    
                    try:
                        # كنأكدو أننا كنصيفطو لـ إيميل الطالب الحقيقي
                        send_mail(subject, msg, 'notif@smartbiblio.com', [request.user.email])
                        emp.rappel_envoye = True
                        emp.save()
                        print(f"✅ Rappel envoyé avec succès à {request.user.email}")
                    except Exception as e:
                        print(f"❌ Erreur Envoi: {e}")

        return render(request, 'gestion_biblio/espace_etudiant.html', {'emprunts': historique})
    except:
        return redirect('register')
 
# --- 3. لوحة تحكم الأدمين ---
@staff_member_required
def dashboard(request):
    total_livres = Livre.objects.count()
    livres_disponibles = Exemplaire.objects.filter(est_disponible=True).count()
    emprunts_actifs = Emprunt.objects.filter(statut='en_cours').count()
 
    stats = Livre.objects.values('categorie').annotate(total=Count('id'))
    
    labels = [s['categorie'] for s in stats if s['categorie']]
    data = [s['total'] for s in stats if s['categorie']]
 
    context = {
        'total': total_livres,
        'disponibles': livres_disponibles,
        'empruntes': emprunts_actifs,
        'labels_js': json.dumps(labels),
        'data_js': json.dumps(data),
        'is_admin': True
    }
    return render(request, 'gestion_biblio/dashboard.html', context)
 
# --- 4. نظام البحث والتوصية ---
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
    selected_category = request.GET.get('category')
    livres = Livre.objects.all()
    all_categories = Livre.objects.values_list('categorie', flat=True).distinct()
 
    if selected_category:
        livres = livres.filter(categorie=selected_category)
 
    # ✅ البحث مصلح
    if query:
        livres = livres.filter(
            Q(titre__icontains=query) |
            Q(auteur__icontains=query) |
            Q(categorie__icontains=query)
        )
 
    for livre in livres:
        livre.disponible = livre.exemplaires.filter(est_disponible=True).exists()
 
    recommandations = get_smart_recommendations(request.user) if request.user.is_authenticated else Livre.objects.all().order_by('?')[:4]
    for r in recommandations:
        r.disponible = r.exemplaires.filter(est_disponible=True).exists()
 
    context = {
        'livres': livres,
        'all_categories': all_categories,
        'selected_category': selected_category,
        'query': query,
        'recommandations': recommandations,
    }
    return render(request, 'gestion_biblio/index.html', context)
 
# --- 5. الحجز والإضافات ---
def detail_livre(request, id):
    livre = get_object_or_404(Livre, id=id)
    dispo = livre.exemplaires.filter(est_disponible=True).exists()
    return render(request, 'gestion_biblio/detail.html', {'livre': livre, 'disponible': dispo})
 
def reserver_livre(request, id):
    if not request.user.is_authenticated: return redirect('register')
    try:
        etudiant = Etudiant.objects.get(user=request.user)
        livre = get_object_or_404(Livre, id=id)
        ex = Exemplaire.objects.filter(livre=livre, est_disponible=True).first()
        if ex:
            ex.est_disponible = False
            ex.save()
            Emprunt.objects.create(etudiant=etudiant, exemplaire=ex, date_retour_prevue=date.today() + timezone.timedelta(days=15))
            messages.success(request, "Votre livre a été réservé ! 📚")
        return redirect('mon_espace')
    except Etudiant.DoesNotExist:
        messages.error(request, "Action réservée aux étudiants.")
        return redirect('home')
 
def annuler_reservation(request, emprunt_id):
    emp = get_object_or_404(Emprunt, id=emprunt_id, etudiant__user=request.user)
    if emp.statut != 'rendu':
        ex = emp.exemplaire
        ex.est_disponible = True
        ex.save()
        emp.delete()
        messages.success(request, "Votre réservation a été annulée. ✅")
    return redirect('mon_espace')
 
def ajouter_note(request, id):
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.info(request, "Veuillez vous inscrire ou vous connecter pour pouvoir noter un livre. 😊")
            return redirect('register')
            
        livre = get_object_or_404(Livre, id=id)
        try:
            etudiant = Etudiant.objects.get(user=request.user)
            valeur = request.POST.get('valeur')
            commentaire = request.POST.get('commentaire')
            Note.objects.create(livre=livre, etudiant=etudiant, valeur=valeur, commentaire=commentaire)
            messages.success(request, "Merci pour votre avis ! ⭐")
        except Etudiant.DoesNotExist:
            messages.error(request, "Action réservée aux étudiants.")
            
    return redirect('detail_livre', id=id)
 
def rejoindre_attente(request, livre_id):
    if not request.user.is_authenticated: return redirect('register')
    livre = get_object_or_404(Livre, id=livre_id)
    try:
        etudiant = Etudiant.objects.get(user=request.user)
        ListeAttente.objects.get_or_create(livre=livre, etudiant=etudiant)
        messages.success(request, "Vous avez été ajouté à la liste d'attente ! 📧")
    except Etudiant.DoesNotExist: pass
    return redirect('detail_livre', id=livre_id)
 
# --- 6. الشات بوت ---
@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            msg = data.get('message', '').strip()
 
            livres = Livre.objects.all().values('titre', 'auteur', 'categorie')
            livres_list = "\n".join([f"- {l['titre']} ({l['categorie']}) par {l['auteur']}" for l in livres])
 
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"""Tu es Smart-Biblio AI, assistant de la bibliothèque Smart-Biblio.
Réponds en français en maximum 2-3 phrases courtes.
Tu comprends aussi l'arabe et le darija marocain.
 
Voici les livres disponibles dans notre bibliothèque :
{livres_list}
 
Base tes recommandations UNIQUEMENT sur ces livres.
Question : {msg}"""}]
            )
            return JsonResponse({'reply': completion.choices[0].message.content})
 
        except Exception as e:
            print(f"System Error: {e}")
            return JsonResponse({'reply': "Désolé, souci technique. 😊"})
 
    return JsonResponse({'reply': 'Erreur'})
 
# --- 7. حذف التعليق ---
def supprimer_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, etudiant__user=request.user)
    livre_id = note.livre.id
    note.delete()
    messages.success(request, "Votre avis a été supprimé. ✅")
    return redirect('detail_livre', id=livre_id)