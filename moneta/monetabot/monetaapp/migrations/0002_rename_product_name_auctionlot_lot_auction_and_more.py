# Generated by Django 4.2.16 on 2024-11-12 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monetaapp', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='auctionlot',
            old_name='product_name',
            new_name='lot_auction',
        ),
        migrations.RenameField(
            model_name='auctionlot',
            old_name='username',
            new_name='user',
        ),
        migrations.AlterField(
            model_name='auction',
            name='lots',
            field=models.ManyToManyField(blank=True, to='monetaapp.auctionlot'),
        ),
        migrations.AlterField(
            model_name='user',
            name='type',
            field=models.CharField(choices=[('User', 'User'), ('Support', 'Support'), ('Seller', 'Seller'), ('Admin', 'Admin')], default='user', max_length=10),
        ),
    ]
