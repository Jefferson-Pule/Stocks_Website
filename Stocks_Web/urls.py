"""
Definition of urls for Stocks_Web.
"""

from datetime import datetime
from django.urls import path, include
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView

from django.conf import settings


from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', include('stock_store.urls')),

    path('account/', include('account.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # Adding Images Path


#from app import forms, views

#urlpatterns = [
#    path('', views.home, name='home'),
#    path('contact/', views.contact, name='contact'),
#    path('about/', views.about, name='about'),
#    path('login/',
#         LoginView.as_view
#         (
#             template_name='app/login.html',
#             authentication_form=forms.BootstrapAuthenticationForm,
#             extra_context=
#             {
#                 'title': 'Log in',
#                 'year' : datetime.now().year,
#             }
#         ),
#         name='login'),
#    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
#    path('admin/', admin.site.urls),
#]
