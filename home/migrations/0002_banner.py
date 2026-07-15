from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=120)),
                ('subtitle', models.CharField(blank=True, max_length=220)),
                ('image', models.ImageField(upload_to='banners/')),
                ('link', models.URLField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['order', 'created_at'], 'verbose_name': 'Banner', 'verbose_name_plural': 'Banners'},
        ),
    ]
