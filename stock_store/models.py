from django.db import models
import pandas as pd
from django.contrib.auth.models import User
import environ
import os
import io

# Create your models here.
class Market_sector(models.Model):

    Sectors=(
        ('E','Energy'),
        ('M', 'Materials'),
        ('I', 'Industrials'),
        ('U', 'Utilities'),
        ('H', 'Healthcare'),
        ('F','Finances'),
        ('CD',"Consumer Discresionary"),
        ('CS', "Consumer Staples"),
        ('IT',"Information Technology"),
        ('C',"Communication Services"),
        ('R',"Real Estate"),
        ('Unk',"Unkown")
        )

    name = models.CharField(max_length = 3, unique = True, choices = Sectors, default = 'Unk')
    slug = models.SlugField(max_length = 3, unique = True)            

    class Meta:

        verbose_name_plural = 'Sectors'

    def __str__(self):
        
        return self.get_name_display()

    @classmethod
    def create(cls, name):
        sector=cls(name=name, slug=name)
        return sector
try:
    Sectors=(
        ('E','Energy'),
        ('M', 'Materials'),
        ('I', 'Industrials'),
        ('U', 'Utilities'),
        ('H', 'Healthcare'),
        ('F','Finances'),
        ('R',"Real Estate"),
        ('CS', "Consumer Staples"),
        ('CD',"Consumer Discresionary"),
        ('IT',"Information Technology"),
        ('C',"Communication Services"),
        ('Unk',"Unkown")
        )

    for sector in Sectors:
        s_i=Market_sector.create(sector[0])
        s_i.save()
except Exception as error:
    pass



class Stock(models.Model):

    stock_local_id = models.AutoField(primary_key = True)       #PK
    
    symbol = models.CharField(max_length = 10, db_index = True)
    
    name = models.CharField(max_length = 251)
    
    sector = models.ForeignKey(Market_sector, related_name = 'stock', on_delete=models.RESTRICT) #FK 

    active = models.BooleanField(default=True)
    
    slug = models.SlugField(max_length = 10, unique = True)

    image = models.ImageField(upload_to='images/')


    class Meta:

        verbose_name_plural = 'Stocks'

    def __str__(self):
        
        return self.symbol
    @classmethod
    def create(cls, symbol, name, active, slug,sector,image=None ):
        stock=cls(symbol=symbol, name=name, active=active, slug=slug,image=image ,sector=sector)
        return stock

try:
    env = environ.Env()
    env.read_env(io.StringIO(os.environ.get("APPLICATION_SETTINGS", None)))
    LOCAL_ENV_PATH=os.environ.get("LOCAL_ENV_PATH", None)
    if LOCAL_ENV_PATH:
        env.read_env(LOCAL_ENV_PATH)

    FIRST_MIGRATE=(env("FIRST_MIGRATE", None)=="True")

    if FIRST_MIGRATE:

        Sec={1:'E', 2:'M', 3:'I', 4:'U', 5:'H', 6:'F',7:'R',8:'CS',9:'CD',10:'IT',11:'C',12:'Unk'}

        SQL_DATA_FILE=env("SQL_DATA_FILE",None)
        
        print(SQL_DATA_FILE)

        df=pd.read_csv(SQL_DATA_FILE, names=["id", "symbol", "name", "active", "slug","image" ,"sector"])

        for i in range(len(df["id"])):

            s_i=Stock.create(symbol=df.iloc[i]["symbol"],name=df.iloc[i]["name"],sector=Market_sector.objects.get(name=Sec[df.iloc[i]["sector"]]),active=df.iloc[i]["active"],slug=df.iloc[i]["slug"])
            s_i.save()

except Exception as e:
    print(e)
    


class Subscription(models.Model):
    user =  models.ForeignKey(User, on_delete=models.CASCADE)
    symbol_subscription = models.ForeignKey(Stock, on_delete=models.CASCADE)

    class Meta:

        verbose_name_plural = 'Subscriptions'
        unique_together = ('user', 'symbol_subscription',)

    def __str__(self):
        return str(self.user)+"-"+str(self.symbol_subscription)