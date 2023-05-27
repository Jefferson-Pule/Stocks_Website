from django.shortcuts import render

from . models import Market_sector, Stock, Subscription
# Create your views here.

def stock_store(request):
    
    if request.user.is_authenticated:
        subscriptions = Subscription.objects.filter(user=request.user)

        # No subscriptions case
        if len(subscriptions)==0:
                    
            slug= 'no-subs'
        else:
            symbol_id = subscriptions.values_list('symbol_subscription_id', flat=True)[0]
            slug = Stock.objects.filter(stock_local_id=symbol_id).values('slug')[0]['slug']
        context={'title':'Home','slug_symbol': slug}
    
    else:
        context={'title':'Home'}

    return render(request, 'stock_store/stock_store.html', context=context)

def market_sector(request):

    all_sectors = Market_sector.objects.all()

    return {'all_sectors': all_sectors}
