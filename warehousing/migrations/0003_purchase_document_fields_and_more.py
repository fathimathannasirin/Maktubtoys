from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehousing', '0002_warehouse_supplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='adjustment',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='purchase',
            name='agreement',
            field=models.CharField(choices=[('Consignment', 'Consignment'), ('Direct Purchase', 'Direct Purchase'), ('Credit', 'Credit')], default='Direct Purchase', max_length=30),
        ),
        migrations.AddField(
            model_name='purchase',
            name='reference_number',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='purchase',
            name='storekeeper',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='purchase',
            name='vat_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='purchaseitem',
            name='old_upc',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='return',
            name='adjustment',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='return',
            name='agreement',
            field=models.CharField(choices=[('Consignment', 'Consignment'), ('Direct Purchase', 'Direct Purchase'), ('Credit', 'Credit')], default='Direct Purchase', max_length=30),
        ),
        migrations.AddField(
            model_name='return',
            name='reference_number',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='return',
            name='storekeeper',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='return',
            name='vat_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='returnitem',
            name='old_upc',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='returnitem',
            name='unit_cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]