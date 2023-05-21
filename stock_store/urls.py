from django.urls import path
from . import views

urlpatterns=[

    path('', views.stock_store, name='stock_store'),
    
    ]
