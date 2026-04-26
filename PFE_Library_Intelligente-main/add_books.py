import os
import django

# إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibliotheque_project.settings')
django.setup()

from gestion_biblio.models import Livre, Exemplaire

def run():
    books_data = [
        # --- INFORMATIQUE & IA ---
        {"titre": "Deep Learning", "auteur": "Ian Goodfellow", "cat": "Informatique", "isbn": "9780262035613", "desc": "La bible de l'apprentissage profond par les pionniers du domaine."},
        {"titre": "Clean Architecture", "auteur": "Robert C. Martin", "cat": "Informatique", "isbn": "9780134494166", "desc": "Un guide universel sur l'organisation du code et des systèmes."},
        {"titre": "Refactoring", "auteur": "Martin Fowler", "cat": "Informatique", "isbn": "9780134757599", "desc": "Améliorer la conception du code existant sans changer son comportement."},
        {"titre": "The Mythical Man-Month", "auteur": "Fred Brooks", "cat": "Informatique", "isbn": "9780201835953", "desc": "Essais classiques sur l'ingénierie logicielle et la gestion de projet."},
        {"titre": "Python Crash Course", "auteur": "Eric Matthes", "cat": "Informatique", "isbn": "9781593279288", "desc": "Une introduction pratique au langage de programmation le plus populaire."},
        {"titre": "Clean Code", "auteur": "Robert C. Martin", "cat": "Informatique", "isbn": "9780132350884", "desc": "Principes et pratiques pour produire du code de haute qualité."},
        {"titre": "Machine Learning Yearning", "auteur": "Andrew Ng", "cat": "Informatique", "isbn": "9780316491976", "desc": "Comment structurer vos projets d'intelligence artificielle."},

        # --- DÉVELOPPEMENT PERSONNEL ---
        {"titre": "Quiet", "auteur": "Susan Cain", "cat": "Développement", "isbn": "9780307352156", "desc": "Le pouvoir des introvertis dans un monde qui ne peut s'arrêter de parler."},
        {"titre": "Essentialism", "auteur": "Greg McKeown", "cat": "Développement", "isbn": "9780316209717", "desc": "La poursuite disciplinée du 'moins mais mieux' pour gagner en efficacité."},
        {"titre": "Deep Work", "auteur": "Cal Newport", "cat": "Développement", "isbn": "9780349411903", "desc": "Règles pour un succès concentré dans un monde de distraction numérique."},
        {"titre": "Ego is the Enemy", "auteur": "Ryan Holiday", "cat": "Développement", "isbn": "9781591847816", "desc": "Pourquoi votre ego est votre plus grand obstacle au succès durable."},
        {"titre": "Atomic Habits", "auteur": "James Clear", "cat": "Développement", "isbn": "9780735211292", "desc": "Comment construire de bonnes habitudes et briser les mauvaises."},

        # --- SCIENCES & PHILOSOPHIE ---
        {"titre": "Meditations", "auteur": "Marcus Aurelius", "cat": "Philosophie", "isbn": "9780140449334", "desc": "Pensées intemporelles de l'empereur romain sur le stoïcisme."},
        {"titre": "The Gene", "auteur": "Siddhartha Mukherjee", "cat": "Science", "isbn": "9781476733500", "desc": "Une histoire intime de la génétique, du passé vers le futur."},
        {"titre": "Pale Blue Dot", "auteur": "Carl Sagan", "cat": "Science", "isbn": "9780345376596", "desc": "Une vision du futur de l'humanité dans l'espace lointain."},
        {"titre": "The Big Picture", "auteur": "Sean Carroll", "cat": "Science", "isbn": "9781101984253", "desc": "Sur l'origine de la vie, le sens et l'univers lui-même."},
        {"titre": "Sophie's World", "auteur": "Jostein Gaarder", "cat": "Philosophie", "isbn": "9780374530716", "desc": "Un roman passionnant sur l'histoire de la philosophie occidentale."},

        # --- ROMANS & LITTÉRATURE ---
        {"titre": "Brave New World", "auteur": "Aldous Huxley", "cat": "Roman", "isbn": "9780060850524", "desc": "Une vision terrifiante d'une société futuriste conditionnée."},
        {"titre": "The Great Gatsby", "auteur": "F. Scott Fitzgerald", "cat": "Roman", "isbn": "9780743273565", "desc": "Le rêve américain et ses désillusions dans les années 20."},
        {"titre": "Moby Dick", "auteur": "Herman Melville", "cat": "Roman", "isbn": "9780142437247", "desc": "La quête obsessionnelle du capitaine Achab contre la baleine blanche."},
        {"titre": "War and Peace", "auteur": "Leo Tolstoy", "cat": "Roman", "isbn": "9780307266934", "desc": "Une épopée magistrale sur la société russe pendant les guerres napoléoniennes."},
        {"titre": "The Alchemist", "auteur": "Paulo Coelho", "cat": "Roman", "isbn": "9780062315007", "desc": "Le voyage d'un berger vers ses rêves à travers le désert égyptien."},
        {"titre": "Crime and Punishment", "auteur": "Fyodor Dostoevsky", "cat": "Roman", "isbn": "9780140449136", "desc": "Une exploration profonde de la morale, du crime et de la rédemption."},
        {"titre": "1984", "auteur": "George Orwell", "cat": "Roman", "isbn": "9780451524935", "desc": "Le classique de la dystopie sur la surveillance et le totalitarisme."},

        # --- BUSINESS & ÉCONOMIE ---
        {"titre": "Blue Ocean Strategy", "auteur": "W. Chan Kim", "cat": "Business", "isbn": "9781591396192", "desc": "Comment créer un nouvel espace de marché et rendre la concurrence inutile."},
        {"titre": "Zero to One", "auteur": "Peter Thiel", "cat": "Business", "isbn": "9780804139298", "desc": "Notes sur les startups et comment construire l'avenir technologique."},
        {"titre": "Shoe Dog", "auteur": "Phil Knight", "cat": "Business", "isbn": "9781501135910", "desc": "L'histoire incroyable de la création de la marque Nike."},
        {"titre": "The Lean Startup", "auteur": "Eric Ries", "cat": "Business", "isbn": "9780307887894", "desc": "Comment l'innovation constante crée des entreprises radicales."},
        {"titre": "Principles", "auteur": "Ray Dalio", "cat": "Business", "isbn": "9781501124020", "desc": "Les règles de vie et de travail du fondateur de Bridgewater."},

        # --- HISTOIRE & BIOGRAPHIE ---
        {"titre": "Sapiens", "auteur": "Yuval Noah Harari", "cat": "Histoire", "isbn": "9780062316097", "desc": "Une brève histoire de l'humanité, des singes aux dieux."},
        {"titre": "The Wright Brothers", "auteur": "David McCullough", "cat": "Histoire", "isbn": "9781476728742", "desc": "L'histoire des pionniers de l'aviation américaine."},
        {"titre": "Steve Jobs", "auteur": "Walter Isaacson", "cat": "Biographie", "isbn": "9781451648539", "desc": "La biographie exclusive du co-fondateur visionnaire d'Apple."},
        {"titre": "Long Walk to Freedom", "auteur": "Nelson Mandela", "cat": "Biographie", "isbn": "9780316548182", "desc": "L'autobiographie inspirante du leader de la lutte contre l'apartheid."},

        # --- PSYCHOLOGIE ---
        {"titre": "Emotional Intelligence", "auteur": "Daniel Goleman", "cat": "Psychologie", "isbn": "9780553383713", "desc": "Pourquoi le quotient émotionnel est plus important que le QI."},
        {"titre": "Flow", "auteur": "Mihaly Csikszentmihalyi", "cat": "Psychologie", "isbn": "9780061339202", "desc": "La psychologie de l'expérience optimale et du bonheur."},
        {"titre": "Man's Search for Meaning", "auteur": "Viktor Frankl", "cat": "Psychologie", "isbn": "9780807014295", "desc": "Survie et espoir dans les camps de concentration nazis."},
        {"titre": "Influence", "auteur": "Robert Cialdini", "cat": "Psychologie", "isbn": "9780061241895", "desc": "La psychologie de la persuasion et comment nous sommes influencés."},
    ]

    for data in books_data:
        # كنكريو الكتاب (أو كنجبدوه إلا كان ديجا كاين باش ما يتعاودش)
        livre, created = Livre.objects.get_or_create(
            titre=data['titre'],
            auteur=data['auteur'],
            isbn=data['isbn'],
            categorie=data['cat'],
            defaults={'description': data['desc']}
        )
        if created:
            # كنزيدو ليه نسخة (Exemplaire)
            Exemplaire.objects.create(
                livre=livre,
                id_exemplaire=f"EXP-{livre.id}-AUTO",
                est_disponible=True
            )
    
    final_count = Livre.objects.count()
    print(f"✅ مبروك يا وصال! السيت دابا فيه {final_count} كتاب.")

if __name__ == "__main__":
    run()