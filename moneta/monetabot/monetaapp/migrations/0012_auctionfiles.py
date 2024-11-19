# Generated by Django 4.2.16 on 2024-11-16 13:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('monetaapp', '0011_remove_auction_product_image_auctionimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuctionFiles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='auction_files')),
                ('auction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='monetaapp.auction')),
            ],
        ),
    ]