from django import forms

from store.models import Product

from .models import PurchaseItem


class ProductCodeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.product_code or str(obj)


class PurchaseItemInlineForm(forms.ModelForm):
    product_code = ProductCodeChoiceField(
        queryset=Product.objects.order_by('product_code'),
        required=False,
        label='Product Code',
    )

    class Meta:
        model = PurchaseItem
        fields = ('product_code', 'product', 'quantity', 'unit_cost', 'received_quantity')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.product_id:
            self.fields['product_code'].initial = self.instance.product_id

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        product_code = cleaned_data.get('product_code')
        if not product and product_code:
            cleaned_data['product'] = product_code
        return cleaned_data
