from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_alter_order_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('New', 'New'), ('Accepted', 'Accepted'), ('Packed', 'Packed'), ('Ready for Preparing', 'Ready for Preparing'), ('Preparing', 'Preparing'), ('Ready for Delivery', 'Ready for Delivery'), ('On The Way', 'On The Way'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='New', max_length=50),
        ),
    ]