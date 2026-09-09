from django.db import migrations


OWN_WAREHOUSE_CODE = 'OWN'
OWN_WAREHOUSE_NAME = 'Own Warehouse'


def create_own_warehouse(apps, schema_editor):
    Warehouse = apps.get_model('warehousing', 'Warehouse')
    if not Warehouse.objects.filter(code=OWN_WAREHOUSE_CODE).exists():
        Warehouse.objects.create(
            supplier=None,
            name=OWN_WAREHOUSE_NAME,
            code=OWN_WAREHOUSE_CODE,
            location='Main Facility',
            is_active=True,
        )


def remove_own_warehouse(apps, schema_editor):
    Warehouse = apps.get_model('warehousing', 'Warehouse')
    Warehouse.objects.filter(code=OWN_WAREHOUSE_CODE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('warehousing', '0003_purchase_document_fields_and_more'),
    ]

    operations = [
        migrations.RunPython(create_own_warehouse, remove_own_warehouse),
    ]
