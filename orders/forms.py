from django import forms
from generalproduct.phone_utils import normalize_qatar_phone
from .models import Order, ReturnRequest


class OrderForm(forms.ModelForm):
    address_line_2 = forms.CharField(required=False)
    order_note = forms.CharField(required=False, widget=forms.Textarea)
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '12345678',
            'inputmode': 'numeric',
            'maxlength': '8',
        }),
    )

    class Meta:
        model = Order
        fields =['first_name', 'last_name', 'phone', 'email', 'address_line_1', 'address_line_2', 'street_number', 'building_number', 'zone_number', 'order_note' ]

    def clean_phone(self):
        return normalize_qatar_phone(self.cleaned_data.get('phone'), required=True)


class ReturnRequestForm(forms.Form):
    reason = forms.ChoiceField(choices=ReturnRequest.RETURN_REASON_CHOICES, required=True)
    description = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 4}))
    return_shipping_acknowledged = forms.BooleanField(required=True)
    policy_terms_accepted = forms.BooleanField(required=True)
        