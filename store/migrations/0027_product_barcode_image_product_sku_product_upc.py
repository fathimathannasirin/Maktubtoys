from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0026_product_cost_price_product_margin_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='barcode_image',
            field=models.ImageField(blank=True, null=True, upload_to='barcodes/products/'),
        ),
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='product',
            name='upc',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
    ]