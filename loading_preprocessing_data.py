import os
import re
import pandas as pd
import geopandas as gpd
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import matplotlib.patches as mpatches
from datetime import datetime
from matplotlib.patches import Polygon as PLG
from shapely.geometry import Point, Polygon
import os


def convert_myJson(data):
    names = data.index.tolist()
    i = 0
    j= 0
    
    to_be_filled = pd.DataFrame()
    for i in range(len(data.index)):
            a = data.iloc[i,:].apply(pd.Series)
            
            current_names = a.columns.tolist()         
            new_names = []
            
            
            for j in range(len(current_names)):
                new_names.append(names[i]+"_"+str(current_names[j]))
                
            a.columns = new_names
            
            to_be_filled = pd.concat([to_be_filled, a],axis=1)
            
    return to_be_filled           


def categorize_colors_by_shipping_fee(df):
    if(df['deliveryFeeDefault'] == 0): 
        return '#e4dbdb'
    elif(df['deliveryFeeDefault'] <= 3.99):
        return '#ffc6a7'
    elif(df['deliveryFeeDefault'] <= 4.99):
        return '#fd6c1d'
    else:
        return 'black'

# Define a function to create a Point from latitude and longitude
def create_point(row):
    return Point(row['location_lng'], row['location_lat'])    


def inside_of_polygon(point,polygon):
    if polygon.contains(point):
        return 'Restaurant inside polygon'
    else:
        return 'Restaurant outside polygon'

def bucket_fee(df):
    if(df['deliveryFeeDefault'] == 0): 
        return '0'
    elif(df['deliveryFeeDefault'] <= 3.99):
        return '<= 3.99'
    elif(df['deliveryFeeDefault'] <= 4.99):
        return '<= 4.99'
    else:
        return '> 5.00'    

def convert_boolean_columns_to_float(df):
    boolean_columns = df.select_dtypes(bool).columns
    if boolean_columns.size > 0:
        df.loc[:, boolean_columns] = df.loc[:, boolean_columns].astype(float)    
    
    
os.chdir('C:/Users/..../Documents/Personal/Lieferando')
f = json.load(open('lieferando_restaurants.json',encoding = 'utf8'))
df = pd.DataFrame(f)
df = convert_myJson(df)


shippingInfo_delivery = df['shippingInfo_delivery'].apply(pd.Series)
shippingInfo_pickup = df['shippingInfo_pickup'].apply(pd.Series)
durationRange = shippingInfo_delivery['durationRange'].apply(pd.Series)
lowestDeliveryFee= shippingInfo_delivery['lowestDeliveryFee'].apply(pd.Series)
distance = shippingInfo_pickup['distance'].apply(pd.Series)

shippingInfo_pickup = shippingInfo_pickup[['isOpenForOrder','isOpenForPreorder','openingTime']]
shippingInfo_delivery = shippingInfo_delivery[['isOpenForOrder','isOpenForPreorder','openingTime','duration','deliveryFeeDefault','minOrderValue']]

df = pd.concat([df,shippingInfo_delivery,durationRange,lowestDeliveryFee,shippingInfo_pickup,distance],axis=1)


df['deliveryFeeDefault'] = df['deliveryFeeDefault']/100
df['minOrderValue'] = df['minOrderValue']/100

df['location_lat']= df['location_lat'].astype(float)
df['location_lng']= df['location_lng'].astype(float)

df['colors'] = df.apply(categorize_colors_by_shipping_fee, axis = 1)