from django.db import migrations, models


def populate_parcel_ids(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    for order in Order.objects.filter(parcel_id__isnull=True).iterator():
        order.parcel_id = f'PCL{order.id:07d}'
        order.save(update_fields=['parcel_id'])


def reverse_populate_parcel_ids(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    Order.objects.update(parcel_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_merge_20260726_0001'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='parcel_id',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.RunPython(populate_parcel_ids, reverse_populate_parcel_ids),
        migrations.AlterField(
            model_name='order',
            name='parcel_id',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
