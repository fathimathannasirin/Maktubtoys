from django import forms
from generalproduct.phone_utils import normalize_qatar_phone
from .models import Account,UserProfile


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Enter password',
        'class': 'form-control',
        'autocomplete': 'new-password',
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Confirm password',
        'class': 'form-control',
        'autocomplete': 'new-password',
    }))
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '12345678',
            'class': 'form-control',
            'inputmode': 'numeric',
            'maxlength': '8',
        }),
    )

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password']
    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder']='Enter First Name'
        self.fields['last_name'].widget.attrs['placeholder']='Enter Last Name'
        self.fields['phone_number'].widget.attrs['placeholder']='12345678'
        self.fields['email'].widget.attrs['placeholder']='Enter Email Address'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] ='form-control'

        if not self.is_bound:
            initial_phone = self.initial.get('phone_number')
            if isinstance(initial_phone, str):
                normalized = initial_phone.strip().replace(' ', '')
                if normalized.startswith('+974'):
                    self.initial['phone_number'] = normalized[4:]
                elif normalized.startswith('974') and len(normalized) == 11:
                    self.initial['phone_number'] = normalized[3:]

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                "Passwords do not match!"
            )

        return cleaned_data

    def clean_phone_number(self):
        return normalize_qatar_phone(self.cleaned_data.get('phone_number'), required=False)

class UserForm(forms.ModelForm):
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '12345678',
            'class': 'form-control',
            'inputmode': 'numeric',
            'maxlength': '8',
        }),
    )

    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] ='form-control'

        if not self.is_bound:
            initial_phone = self.initial.get('phone_number')
            if isinstance(initial_phone, str):
                normalized = initial_phone.strip().replace(' ', '')
                if normalized.startswith('+974'):
                    self.initial['phone_number'] = normalized[4:]
                elif normalized.startswith('974') and len(normalized) == 11:
                    self.initial['phone_number'] = normalized[3:]

    def clean_phone_number(self):
        return normalize_qatar_phone(self.cleaned_data.get('phone_number'), required=False)

class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, error_messages={'invalid':("Image files only")}, widget=forms.FileInput)
    class Meta:
        model = UserProfile
        fields = ('address_line_1', 'address_line_2','street_number', 'building_number', 'zone_number', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] ='form-control'
