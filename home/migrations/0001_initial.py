from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(help_text='Message to display in the scrolling announcement bar', max_length=220)),
                ('is_active', models.BooleanField(default=True, help_text='Show this message on the site')),
                ('order', models.PositiveIntegerField(default=0, help_text='Lower numbers appear first')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['order', 'created_at'],
                'verbose_name': 'Announcement',
                'verbose_name_plural': 'Announcements',
            },
        ),
    ]
