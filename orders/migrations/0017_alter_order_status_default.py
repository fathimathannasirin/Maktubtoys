from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0016_normalize_legacy_parcel_statuses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('Processing', 'Processing'),
                    ('Collecting', 'Collecting'),
                    ('Ready for Preparing', 'Ready for Preparing'),
                    ('Preparing', 'Preparing'),
                    ('Ready for Delivery', 'Ready for Delivery'),
                    ('On The Way', 'On The Way'),
                    ('Delivered', 'Delivered'),
                    ('Cancelled', 'Cancelled'),
                ],
                default='Processing',
                max_length=50,
            ),
        ),
    ]