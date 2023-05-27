from django.shortcuts import render, redirect

from .forms import CreateUserForm, LoginForm

from django.contrib.auth.models import auth

from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.decorators import login_required

from django.contrib import messages

from stock_store.models import Subscription, Stock, Market_sector

from django.db.models import Count, Q

from django.shortcuts import get_object_or_404

from django.http import JsonResponse
from django.core import serializers

import os
import json
import environ

from .bigquery import BigqueryClass

from random import randint
from time import time

# Create your views here.

# Register
def register(request):
    
    form = CreateUserForm()

    if request.method == 'POST':
        
        form = CreateUserForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect('my-login')

    context = {'title':'Register','form': form}

    return render(request, 'account/register.html', context = context)

# Login
def my_login(request):
    
    form = LoginForm()

    if request.method == 'POST':
        
        form = LoginForm(request, data=request.POST)

        if form.is_valid():

            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username = username, password = password)

            if user is not None:
                auth.login(request, user)

                subscriptions = Subscription.objects.filter(user=request.user)

                # No subscriptions case
                if len(subscriptions)==0:
                    
                    slug= 'no-subs'
                    
                    return redirect("dashboard/"+slug)

                symbol_id = subscriptions.values_list('symbol_subscription_id', flat=True)[0]
                

                slug = Stock.objects.filter(stock_local_id=symbol_id).values('slug')[0]['slug']
                #print(slug)
                return redirect("dashboard/"+slug)

    context = {'title':'Login','form': form }

    return render(request, 'account/my-login.html', context = context)

# Logout
def user_logout(request):
    auth.logout(request)

    messages.success(request, "Logout success")

    return redirect("stock_store")

# Explore
@login_required(login_url='my-login')
def explore(request):
    # Values
    
    LOCAL_ENV_PATH=os.environ.get("LOCAL_ENV_PATH", None)
    env = environ.Env()

    if LOCAL_ENV_PATH:               
        env.read_env(LOCAL_ENV_PATH)

    key_location = env("BIG_QUERY_LOCATION", default=r"/secret/Bigquery_key")
    n_total = 10
    n = 10
    # Big query for table
    user_subs_obj = Subscription.objects.filter(user=request.user)
    user_subs_id = user_subs_obj.values_list('symbol_subscription_id', flat=True)

    no_user_subs_obj = Stock.objects.exclude(stock_local_id__in = user_subs_id)
    no_user_subs_id = no_user_subs_obj.values_list('stock_local_id', flat=True)
    
    #print("id",user_subs_id, no_user_subs_id)

    Bq = BigqueryClass(n_total=n_total, n=n)

    data_subs = Bq.get_bq_data(user_subs_id, key_location)
    data_no_subs = Bq.get_bq_data(no_user_subs_id, key_location)

    data = {"data_subs": Bq.generate_table_data(data_subs["result_n_day"], subscription=True), "data_no_subs": Bq.generate_table_data(data_no_subs["result_n_day"], subscription=False)}

    #print(data)

    context =  {'user': request.user,
                'user_subscriptions' : data, # Data for explore table
                }

    # Ajax response

    if request.method == 'POST':

        symbol_to_update = request.POST.get('symbol')
        action_to_do = int(request.POST.get('action'))

        if action_to_do == 1:

            symbol_id_to_update = Stock.objects.filter(symbol=symbol_to_update).values('stock_local_id')[0]['stock_local_id']
            delete_sub = Subscription.objects.filter(user=request.user.id, symbol_subscription= symbol_id_to_update).delete()
           # print("subscription deleted ",request.user.username, symbol_to_update, delete_sub)

        else:

            symbol_id_to_update = Stock.objects.filter(symbol=symbol_to_update)[0]                       
            create_sub = Subscription(user=request.user, symbol_subscription = symbol_id_to_update)
            create_sub.save()
            #print(" subscription created ", request.user.username, symbol_to_update)

        return JsonResponse({'seconds': time()}, status = 200)


    return render(request,'account/explore.html', context)

# Dashboard
@login_required(login_url='my-login')
def dashboard(request, slug):
    # No subscriptions setting
    if len(Subscription.objects.filter(user=request.user)) == 0:
        messages.success(request, "Add some subscriptions to see the Dashboard")
        return redirect('explore')

    elif slug == '':
        first_symbol_id=Subscription.objects.filter(user=request.user).values('symbol_subscription_id')[0]['symbol_subscription_id']
       # print(first_symbol_id)
        slug = Stock.objects.filter(stock_local_id=first_symbol_id).values('slug')[0]['slug']


    slug_symbol=get_object_or_404(Stock, symbol=slug)

    Stk_objc=Stock.objects.filter(symbol=slug_symbol)

    slug_symbol_id = Stk_objc.values('stock_local_id')[0]['stock_local_id']

    slug_name= Stk_objc.values('name')[0]['name']
    #print(Stk_objc.values('sector_id')[0]['sector_id'])
    slug_market= Market_sector.objects.get(id = Stk_objc.values('sector_id')[0]['sector_id']) 
    # Ajax response

    if request.method == 'POST':

        symbol_to_update = request.POST.get('symbol')
        action_to_do = int(request.POST.get('action'))

        if action_to_do == 1:

            symbol_id_to_update = Stock.objects.filter(symbol=symbol_to_update).values('stock_local_id')[0]['stock_local_id']
            delete_sub = Subscription.objects.filter(user=request.user.id, symbol_subscription= symbol_id_to_update).delete()
           # print("subscription deleted ",request.user.username, symbol_to_update, delete_sub)

        else:

            symbol_id_to_update = Stock.objects.filter(symbol=symbol_to_update)[0]                       
            create_sub = Subscription(user=request.user, symbol_subscription = symbol_id_to_update)
            create_sub.save()
           # print(" subscription created ", request.user.username, symbol_to_update)

        return JsonResponse({'seconds': time()}, status = 200)

    # Values
    LOCAL_ENV_PATH=os.environ.get("LOCAL_ENV_PATH", None)
    env = environ.Env()

    if LOCAL_ENV_PATH:               
        env.read_env(LOCAL_ENV_PATH)

    key_location = env("BIG_QUERY_LOCATION", default=r"/secret/Bigquery_key")
    n_total = 365
    n = 10


    # Big query for main chart and table
    user_subs_obj = Subscription.objects.filter(user=request.user)
    user_subs_id = user_subs_obj.values_list('symbol_subscription_id', flat=True)

    #print("sl_", slug_symbol_id)    
    Bq = BigqueryClass(n_total=n_total, n=n)

    data = Bq.get_bq_data(user_subs_id, key_location, slug_symbol_id)

    # Diversity Chart
    dc_stocks_obj = Stock.objects.filter(stock_local_id__in=user_subs_obj.values('symbol_subscription_id'))
        
    dc_stocks_in_sector = list(dc_stocks_obj.values("sector_id").annotate(Count("sector_id")))
    dc_market_sectors_obj = Market_sector.objects.filter(id__in=dc_stocks_obj.values('sector_id'))
    dc_dictionary = list(dc_market_sectors_obj.values_list('id', 'name').values('id', 'name'))

    dc_labels=[]
    dc_count=[]
    dic={}
    
    for k in dc_dictionary:
        dic.update(k)

    for i, sector in enumerate(dc_stocks_in_sector):
        dc_count.append(sector["sector_id__count"])
        dc_labels.append(Market_sector.objects.get(id=sector["sector_id"]).get_name_display())

    
    dc_data={"data": dc_count, "labels": dc_labels}

    #print(data["result_n_total"])
    
    context =  {'user': request.user,
                'slug_symbol': slug_symbol,
                'slug_name': slug_name,
                'slug_market': slug_market,
                'user_subscriptions' : Bq.generate_table_data(data["result_n_day"]), # Data for main table
                'slug_data' : Bq.generate_chart_data(data["result_n_total"]), # Data for main chart
                "dc_data": dc_data # Data for Diversity Chart
                }
    #print(context['user_subscriptions'][-4],type(context['user_subscriptions']))

    #dc_labels = list(map(Market_sector.get_name_display,list(dc_market_sectors_obj)))


        ##'dc_labels': dc_labels , # Diversity Chart labels
        ##'dc_dictionary': dc_dictionary, # Diversity Chart From id to let
        ##'dc_stocks_in_sector': dc_stocks_in_sector # Diversity User subscriptions 

    #from random import random
    
    #fake_chart_data=[{'Date': ['2023-03-16T00:00:00+00:00', '2023-03-15T00:00:00+00:00', '2023-03-14T00:00:00+00:00', '2023-03-13T00:00:00+00:00', '2023-03-10T00:00:00+00:00', '2023-03-09T00:00:00+00:00', '2023-03-08T00:00:00+00:00', '2023-03-07T00:00:00+00:00', '2023-03-06T00:00:00+00:00', '2023-03-03T00:00:00+00:00'],\
    #   'Open': [152.1600036621, 151.1900024414, 151.2799987793, 147.8099975586, 150.2100067139, 153.5599975586, 152.8099975586, 153.6999969482, 153.7899932861, 148.0399932861],\
    #   'High': [156.4600067139, 153.25, 153.3999938965, 153.1399993896, 150.9400024414, 154.5399932861, 153.4700012207, 154.0299987793, 156.3000030518, 151.1100006104],\
    #   'Low': [151.6399993896, 149.9199981689, 150.1000061035, 147.6999969482, 147.6100006104, 150.2299957275, 151.8300018311, 151.1300048828, 153.4600067139, 147.3300018311], \
    #   'Adj_Close': [155.8500061035, 152.9900054932, 152.5899963379, 150.4700012207, 148.5, 150.5899963379, 152.8699951172, 151.6000061035, 153.8300018311, 151.0299987793], \
    #   'Volume': [76254400.0, 77167900.0, 73695900.0, 84457100.0, 68524400.0, 53833600.0, 47204800.0, 56182000.0, 87558000.0, 70668500.0],\
    #   'Close': [155.8500061035, 152.9900054932, 152.5899963379, 150.4700012207, 148.5, 150.5899963379, 152.8699951172, 151.6000061035, 153.8300018311, 151.0299987793]}]

    #l=[]
    #for i in range(50):
    #    l.append({"symbol": "googl", "name": "google", "date": "2023-03-16t00:00:00+00:00", "open": 96.1999969482, "high": 101.1900024414, "low": 95.5, "close": 100.3199996948, "adj_close": 100.3199996948, "volume": 65567700.0, "line": [90.6299972534, 91.1100006104, 93.9700012207, 96.1100006104, 100.3199996948, 1], "user_subscribed": randint(0, 1)})
    #    l.append({"symbol": "aapl", "name": "apple inc", "date": "2023-03-16t00:00:00+00:00", "open": 96.1999969482, "high": 101.1900024414, "low": 95.5, "close": 100.3199996948, "adj_close": 100.3199996948, "volume": 65567700.0, "line": [90.6299972534, 91.1100006104, 93.9700012207, 96.1100006104, 100.3199996948, 1], "user_subscribed": randint(0, 1)})
    #fake_data_table=json.dumps(l)

    #context =  {'user': request.user,
    #            'user_subscriptions' : fake_data_table,
    #            'slug_data' : fake_chart_data,
    #            'slug_symbol': slug_symbol
    #            }    
 
    return render(request,'account/dashboard.html',context=context)