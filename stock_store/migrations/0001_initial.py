# Generated by Django 4.1.7 on 2023-05-20 07:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Market_sector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('E', 'Energy'), ('M', 'Materials'), ('I', 'Industrials'), ('U', 'Utilities'), ('H', 'Healthcare'), ('F', 'Finances'), ('CD', 'Consumer Discresionary'), ('CS', 'Consumer Staples'), ('IT', 'Information Technology'), ('C', 'Communication Services'), ('R', 'Real Estate'), ('Unk', 'Unkown')], default='Unk', max_length=3, unique=True)),
                ('slug', models.SlugField(max_length=3, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Sectors',
            },
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('stock_local_id', models.AutoField(primary_key=True, serialize=False)),
                ('symbol', models.CharField(db_index=True, max_length=10)),
                ('name', models.CharField(max_length=251)),
                ('active', models.BooleanField(default=True)),
                ('slug', models.SlugField(max_length=10, unique=True)),
                ('image', models.ImageField(upload_to='images/')),
                ('sector', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='stock', to='stock_store.market_sector')),
            ],
            options={
                'verbose_name_plural': 'Stocks',
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol_subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock_store.stock')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Subscriptions',
                'unique_together': {('user', 'symbol_subscription')},
            },
        ),
    ]
