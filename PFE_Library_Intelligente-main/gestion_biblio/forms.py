from django import forms
from django.contrib.auth.models import User
from .models import Etudiant
from django import forms

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    cne = forms.CharField(max_length=20, label="CNE (Massar)")
    
    # هنا رديناها ChoiceField باش تطلع القائمة
    niveau_etude = forms.ChoiceField(
        choices=Etudiant.NIVEAU_CHOICES, 
        label="Niveau d'étude & Filière"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        # forms.py


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control rounded-pill border-0 shadow-sm px-4',
        'placeholder': 'Nom d\'utilisateur'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control rounded-pill border-0 shadow-sm px-4',
        'placeholder': 'Mot de passe'
    }))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            Etudiant.objects.create(
                user=user,
                cne=self.cleaned_data['cne'],
                niveau_etude=self.cleaned_data['niveau_etude']
            )
        return user