from django.contrib import admin

# Register your models here.
from . models import Market_sector, Stock, Subscription

@admin.register(Market_sector)
class Market_sectorAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ['name',]}

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ['symbol',]}

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    pass
