from django.urls import path, re_path
from . import views

urlpatterns=[
    # Register urls

    path('register', views.register, name='register'),

    # Login / Logout urls
    path('my-login', views.my_login, name = 'my-login'),

    path('user-logout', views.user_logout, name='user-logout'),

    path('explore', views.explore, name = 'explore'),
    # Dashboard

    #path('dashboard/<slug:slug>', views.dashboard, name = 'dashboard'),

    re_path(r'dashboard/(?P<slug>[-\w]*)/$', views.dashboard, name='dashboard'),
    ]

