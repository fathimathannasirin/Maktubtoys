import re

from django.db import migrations, models


def copy_age_category_names_to_age(apps, schema_editor):
    Product = apps.get_model('store', 'Product')

    for product in Product.objects.select_related('age_category').all():
        age_category = getattr(product, 'age_category', None)
        if not age_category or not age_category.name:
            continue

        match = re.search(r'\d+', age_category.name)
        if not match:
            continue

        product.age = int(match.group())
        product.save(update_fields=['age'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0024_agecategory_product_age_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='age',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(copy_age_category_names_to_age, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='product',
            name='age_category',
        ),
        migrations.DeleteModel(
            name='AgeCategory',
        ),
    ]