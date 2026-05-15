from modeltranslation.translator import register, TranslationOptions
from .models import Product, Category

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('category_name', 'description')

@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('product_name', 'description')