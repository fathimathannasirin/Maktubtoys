from django.db import migrations


def normalize_legacy_parcel_statuses(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    status_mapping = {
        'New': 'Processing',
        'Accepted': 'Delivered',
        'Packed': 'Collecting',
        'Completed': 'Delivered',
    }
    for old_status, new_status in status_mapping.items():
        Order.objects.filter(status=old_status).update(status=new_status)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0015_alter_order_status'),
    ]

    operations = [
        migrations.RunPython(normalize_legacy_parcel_statuses, migrations.RunPython.noop),
    ]