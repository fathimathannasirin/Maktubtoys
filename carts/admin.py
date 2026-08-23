from django.contrib import admin
from .models import Cart, CartItem

class BaseAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/admin_form_validation.js',)

class CartAdmin(BaseAdmin,admin.ModelAdmin):
    list_display = ('cart_id', 'date_added')

class CartItemAdmin(BaseAdmin,admin.ModelAdmin):
    # Ensure there are no leading spaces in 'get_variations'
    list_display = ('product', 'get_variations', 'cart', 'quantity', 'is_active')
    search_fields = ['product', 'get_variations', 'cart', 'quantity']

    # IMPORTANT: This function MUST be indented 4 spaces (inside the class)
    def get_variations(self, obj):
        # This reaches into the ManyToMany variations field defined in your models.py
        return ", ".join([str(v.variation_value) for v in obj.variations.all()])
    
    get_variations.short_description = 'Variations'

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)