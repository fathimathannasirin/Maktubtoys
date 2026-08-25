from django import forms
from .models import ReviewRating, Product


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject', 'review', 'rating']


class ProductForm(forms.ModelForm):
    """Custom Product form with purchase items linking and margin calculation"""
    purchase_item_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_purchase_item_id',
            'placeholder': 'Select from purchase items...',
            'class': 'form-control'
        }),
        label='Link to Purchase Item (Optional)'
    )
    
    class Meta:
        model = Product
        fields = [
            'product_name', 'slug', 'description', 'price', 'cost_price',
            'images', 'stock', 'category', 'age', 'supplier', 'warehouse',
            'is_available', 'margin_amount', 'margin_percentage'
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_price'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_cost_price'}),
            'images': forms.FileInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'margin_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'step': '0.01', 'id': 'id_margin_amount'}),
            'margin_percentage': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'step': '0.01', 'id': 'id_margin_percentage'}),
        }