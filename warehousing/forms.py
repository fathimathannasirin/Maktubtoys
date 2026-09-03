from django import forms
from store.models import Product
from .models import PurchaseItem, ReturnItem


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
        fields = ('product_code', 'product', 'old_upc', 'quantity', 'unit_cost', 'received_quantity')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        product_qs = Product.objects.all()
        if self.instance and self.instance.pk and self.instance.purchase:
            purchase = self.instance.purchase
            if purchase.supplier:
                product_qs = product_qs.filter(supplier=purchase.supplier)
            if purchase.warehouse:
                product_qs = product_qs.filter(warehouse=purchase.warehouse)

        self.fields['product'].queryset = product_qs
        self.fields['product_code'].queryset = product_qs

        if self.instance and self.instance.pk and self.instance.product_id:
            self.fields['product_code'].initial = self.instance.product_id

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        product_code = cleaned_data.get('product_code')
        if not product and product_code:
            cleaned_data['product'] = product_code
        return cleaned_data




class ReturnItemInlineForm(forms.ModelForm):
    product_code = ProductCodeChoiceField(
        queryset=Product.objects.order_by('product_code'),
        required=False,
        label='Product Code',
    )

    class Meta:
        model = ReturnItem
        fields = ('product_code', 'product', 'old_upc', 'quantity', 'unit_cost', 'notes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product_qs = Product.objects.all()

        if self.instance and self.instance.pk and self.instance.return_record:
            return_rec = self.instance.return_record
            if return_rec.supplier:
                product_qs = product_qs.filter(supplier=return_rec.supplier)
            if return_rec.warehouse:
                product_qs = product_qs.filter(warehouse=return_rec.warehouse)

        self.fields['product'].queryset = product_qs
        self.fields['product_code'].queryset = product_qs
        
        if self.instance and self.instance.pk and self.instance.product_id:
            self.fields['product_code'].initial = self.instance.product_id

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        product_code = cleaned_data.get('product_code')
        if not product and product_code:
            cleaned_data['product'] = product_code
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dropdown-ൽ Product-ന്റെ Code കാണിക്കാൻ
        self.fields['product_code'].label_from_instance = lambda obj: f"{obj.product_code}"
        if self.instance and self.instance.pk and self.instance.product:
            self.fields['product_code'].initial = self.instance.product