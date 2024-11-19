# Generated by Django 4.2.16 on 2024-11-18 08:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('monetaapp', '0014_user_seller_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoBid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_bid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('auction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auto_bids', to='monetaapp.auction')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auto_bids', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
