from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.core.management import call_command

# 1. صاوبنا دالة عندها سمية حقيقية بلاصة lambda
def send_due_date_emails():
    call_command('notifier_delai')

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # 2. كنستعملو سمية الدالة مباشرة هنا
    scheduler.add_job(
        send_due_date_emails, # السمية ديال الدالة اللي صاوبنا لفوق
        'interval',
        minutes=1, # دبا غايجرب كل دقيقة
        name='envoi_rappels',
        jobstore='default',
        replace_existing=True,
    )

    scheduler.start()
    print("✅ Scheduler bda khdam... l-mails ghay-tsifto rasha!")