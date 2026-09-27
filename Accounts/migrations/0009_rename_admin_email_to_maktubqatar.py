from django.db import migrations


OLD_EMAIL = 'ayyothjasna@gmail.com'
NEW_EMAIL = 'Info@maktubqatar.com'


def forwards(apps, schema_editor):
    Account = apps.get_model('Accounts', 'Account')
    Account.objects.filter(email__iexact=OLD_EMAIL).update(
        email=NEW_EMAIL,
        username=NEW_EMAIL,
    )


def backwards(apps, schema_editor):
    Account = apps.get_model('Accounts', 'Account')
    Account.objects.filter(email__iexact=NEW_EMAIL).update(
        email=OLD_EMAIL,
        username=OLD_EMAIL,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('Accounts', '0008_account_is_superuser'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
