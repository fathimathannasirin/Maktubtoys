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

    def __init__(self, *args, supplier_id=None, **kwargs):
        super().__init__(*args, **kwargs)

        product_qs = Product.objects.all().order_by('product_name')
        if not supplier_id and self.instance and self.instance.pk and self.instance.purchase:
            supplier_id = self.instance.purchase.supplier_id
        if supplier_id:
            product_qs = product_qs.filter(supplier_id=supplier_id)

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

        quantity = cleaned_data.get('quantity')
        received_quantity = cleaned_data.get('received_quantity')
        if (
            quantity is not None
            and received_quantity is not None
            and received_quantity > quantity
        ):
            self.add_error(
                'received_quantity',
                'Received quantity cannot be greater than the ordered quantity.',
            )
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

    def __init__(self, *args, supplier_id=None, warehouse_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        product_qs = Product.objects.all().order_by('product_name')

        if self.instance and self.instance.pk and self.instance.return_record:
            return_rec = self.instance.return_record
            supplier_id = supplier_id or return_rec.supplier_id
            warehouse_id = warehouse_id or return_rec.warehouse_id

        if supplier_id or warehouse_id:
            purchased_items = PurchaseItem.objects.all()
            if supplier_id:
                purchased_items = purchased_items.filter(purchase__supplier_id=supplier_id)
            if warehouse_id:
                purchased_items = purchased_items.filter(purchase__warehouse_id=warehouse_id)
            product_qs = product_qs.filter(id__in=purchased_items.values_list('product_id', flat=True).distinct())

        self.fields['product'].queryset = product_qs
        self.fields['product_code'].queryset = product_qs
        self.fields['product_code'].label_from_instance = lambda obj: f"{obj.product_code}"

        if self.instance and self.instance.pk and self.instance.product_id:
            self.fields['product_code'].initial = self.instance.product_id

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        product_code = cleaned_data.get('product_code')
        if not product and product_code:
            cleaned_data['product'] = product_code
        return cleaned_data