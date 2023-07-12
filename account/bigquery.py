import pandas as pd
import json 
from datetime import date

from google.cloud import bigquery

import environ
import os
import io

class BigqueryClass:
    def __init__(self, n_total, n):
        self.n_total = n_total
        self.n = n

    def user_to_set(self, user_subs_id):
       
        subs_set="("

        for subs_id in user_subs_id:
        
            subs_set=subs_set+str(subs_id)+","
    
        subs_set=subs_set[:-1]+")"
        return subs_set

    def query_from_bq(self, key_location, bq_query, data_frame=False):
        ## Google related information

        #SERVICE_ACCOUNT_JSON= key_location
        
        ## Call the client
        #client=bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_JSON)
        env = environ.Env()
        env.read_env(io.StringIO(os.environ.get("APPLICATION_SETTINGS", None)))

        LOCAL_ENV_PATH=os.environ.get("LOCAL_ENV_PATH", None)
        if LOCAL_ENV_PATH:
            env.read_env(LOCAL_ENV_PATH)

        PROJECT_ID=env("PROJECT_ID", default=None)

        client=bigquery.Client(project=PROJECT_ID)

        # Query
        query_job = client.query(bq_query)                                                    
        
        if data_frame:
            result = query_job.to_dataframe()
        else:
            result = list(query_job.result())

        return result

    def create_queries(self, subs_set, n_total, n, symbol_id):
        # Load the settings from the environment variable
        env = environ.Env()
        env.read_env(io.StringIO(os.environ.get("APPLICATION_SETTINGS", None)))

        LOCAL_ENV_PATH=os.environ.get("LOCAL_ENV_PATH", None)
        
        if LOCAL_ENV_PATH:
            env.read_env(LOCAL_ENV_PATH)

        PROJECT_ID=env("PROJECT_ID", default=None)

        client=bigquery.Client(project=PROJECT_ID)
        print(client.project, "###################")
        query_for_stock_graph=f"""
        SELECT *, Moving_average+2*Std AS UpBoll, Moving_average-2*Std AS DownBoll FROM
            (SELECT *, avg(data.close) OVER(ORDER BY data.Date Asc ROWS BETWEEN 20 PRECEDING AND CURRENT ROW ) as Moving_average,  
            IFNULL(STDDEV(data.close) OVER(ORDER BY data.Date Asc ROWS BETWEEN 20 PRECEDING AND CURRENT ROW ),0) as Std 
            
            FROM UNNEST((

                    SELECT INFO FROM `{client.project}.Stocks_dataset.Stocks_info` 
                    WHERE Symbol_id= {symbol_id}
            ))
                   
            AS data ORDER BY Date DESC LIMIT {n_total}
            )
            """

        query_for_n_days_closing=f"""
                SELECT * FROM (

                    SELECT Symbol, Name,I.Date AS Date, I.Open AS Open, I.High AS High, I.Low AS Low, 
                    I.Close AS Close, I.Adj_Close AS Adj_Close, I.Volume AS Volume, 
                    row_number() over (partition by Symbol_ID order by Symbol, I.Date DESC) As Date_rank 
                    From `{client.project}.Stocks_dataset.Stocks_info` CROSS JOIN UNNEST(Info) AS I 
                    WHERE Symbol_ID IN {subs_set} 

                ) WHERE Date_rank<={n}
              """
       # print(query_for_stock_graph)
       # print(query_for_n_days_closing)
        return {"result_n_total": query_for_stock_graph, "result_n_day": query_for_n_days_closing}

    def get_bq_data(self, user_subs_id, key_location, symbol_id=0):
           
        # No Subscriptions or symbol_id not integer
        if len(user_subs_id)==0 or not (type(symbol_id) is int) :
            return {"result_n_total": pd.DataFrame([]), "result_n_day":[]}
        
        n_total = self.n_total
        n = self.n

        subs_set=self.user_to_set(user_subs_id)

        queries=self.create_queries(subs_set, n_total, n, symbol_id)

        # If symbol not given then do not query 
        if symbol_id==0:
            queries.pop('result_n_total')
    
        bq_data={}

        data_frame=False
        
        for key, query in queries.items():

            if key=="result_n_total":
                # Return dataframe 

                data_frame=True
                bq_data[key]=self.query_from_bq(key_location, query, data_frame)
                data_frame=False

            else:
                bq_data[key]=self.query_from_bq(key_location, query, data_frame)

        return bq_data

    # Generate table data
    def generate_table_data(self, data, subscription=True):
        
        if len(data)==0:
            return json.dumps(data)


        if subscription:
            subs_byte=1
        else:
            subs_byte=0

        n=self.n
        symbols_info=[]
        n_day_close=[]

        row=0
        row_symbol=""
        k=0

        while row<len(data):
            # Transform data to proper form 

            if row_symbol != data[row][0]:

                row_symbol = data[row][0]
        #        print("changed symbol", row_symbol,"row" ,row)     
          
                symbol_info={'Symbol': data[row][0], 'Name': data[row][1], 'Date': data[row][2].isoformat(), \
                             'Open': data[row][3], 'High': data[row][4], 'Low': data[row][5], \
                             'Close': data[row][6], 'Adj_Close': data[row][7], 'Volume': data[row][8], 'User_subscribed': subs_byte}

                maxi=data[row][6]
                mini=data[row][6]
               
               # Get 5 days data
                while row<len(data) and k<n and row_symbol == data[row][0]:

                    # Add close
                    row_symbol = data[row][0]
                    close=data[row][6]
                    n_day_close.append(close)

                    # Calculate max and min

                    if close>maxi:
                        maxi=close
                    if close<mini:
                        mini=close
     
                    k+=1
                    row+=1

                # Reverse Order
                n_day_close.reverse()

                # Append max and min
                n_day_close.append(mini) # min in -3
                n_day_close.append(maxi) # max in -2

                # Add Color 
                difference=n_day_close[-3]-n_day_close[-4] 
                #print(difference)
                if difference>0:
                    colour=1

                elif difference==0:
                    colour=0

                else:
                    colour=-1

                n_day_close.append(colour)     # color in -1

                # Add to dictionary 
                symbol_info["line"] = n_day_close
                row-=1

            symbols_info.append(symbol_info)
            k=0
            n_day_close=[]
            row_symbol = data[row][0]
            row+=1

        return json.dumps(symbols_info)

    # Geta data for chart 
    
    def generate_chart_data(self, data):


        data.sort_values(by="Date", ascending=True, inplace=True)

        fields=[]
        field={}
        for key in data:
   
            if key=="Date":
                field[key]=data[key].apply(lambda x: pd.Timestamp.isoformat(x)).tolist()
            else:       
                field[key]=data[key].tolist()

        fields.append(field)

        return fields