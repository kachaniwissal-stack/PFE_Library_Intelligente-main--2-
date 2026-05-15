from django import forms
from django.contrib.auth.models import User
from .models import Etudiant, EtudiantAutorise
from django.core.exceptions import ValidationError

class RegisterForm(forms.ModelForm):
    # تعريف الخانات اللي غيبانو في الصفحة
    first_name = forms.CharField(label="Prénom", required=True)
    last_name = forms.CharField(label="Nom", required=True)
    email = forms.EmailField(label="Adresse électronique (Gmail)", required=True)
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe", required=True)
    cne = forms.CharField(max_length=20, label="Code Apogée", required=True)
    
    niveau_etude = forms.ChoiceField(
    # هنا كنلصقو الاختيار الخاوي مع الاختيارات اللي فـ الموديل
    choices=[('', ' Choisir la filière ')] + list(Etudiant.NIVEAU_CHOICES), 
    label="Filière",
    required=True # باش بزز عليه يختار وحدة وما يخليهاش خاوية
)

    class Meta:
        model = User
        # ضروري نزيدو username هنا باش Django يقبلو، ولكن غنخبّيوه
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        # هادي هي أهم لقطة: كنقولو لـ Django أن username ماشي إجباري فـ الـ Form
        self.fields['username'].required = False
        self.fields['username'].widget = forms.HiddenInput() # كيبقى مخفي

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        
        # كنعطيو لـ username قيمة الـ email قبل ما يدوز الـ Validation
        if email:
            cleaned_data['username'] = email
            # كنشوفو واش هاد الإيميل ديجا مسجل كـ username
            if User.objects.filter(username=email).exists():
                self.add_error('email', "Cet email est déjà utilisé.")
        return cleaned_data

    def clean_cne(self):
        code = self.cleaned_data.get('cne')
        
        # 1. كنشوفو واش الكود كاين أصلاً فـ اللائحة الرسمية
        exists_in_authorized = EtudiantAutorise.objects.filter(code_apogee=code).exists()
        if not exists_in_authorized:
            raise ValidationError("Ce Code Apogée n'est pas reconnu par la base de données de la faculté.")

        # 2. (الزيادة الجديدة) كنشوفو واش ديجا شي طالب مسجل بهاد الكود
        if Etudiant.objects.filter(cne=code).exists():
            raise ValidationError("Ce Code Apogée est déjà utilisé pour un autre compte.")

        return code   

    def save(self, commit=True):
        user = super().save(commit=False)
        # كنزيدو نأكدو أن username هو الإيميل فاش نبغيو نسجلو فـ الداتابيز
        user.username = self.cleaned_data.get('email')
        user.set_password(self.cleaned_data["password"])
        
        if commit:
            user.save()
            # إنشاء بروفايل الطالب (Etudiant)
            # استعملت get_or_create باش ما يوقعش Error ديال التكرار مع الـ View
            Etudiant.objects.get_or_create(
                user=user,
                defaults={
                    'cne': self.cleaned_data.get('cne'),
                    'niveau_etude': self.cleaned_data.get('niveau_etude')
                }
            )
        return user