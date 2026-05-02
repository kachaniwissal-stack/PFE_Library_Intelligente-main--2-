from django.apps import AppConfig

class GestionBiblioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_biblio'

    def ready(self):
        # هاد السطر كيخلي الـ scheduler يبدا غير فاش السيرفر يقلع
        import os
        if os.environ.get('RUN_MAIN'):
            from . import operator
            operator.start()