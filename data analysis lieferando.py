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


def categorize_colors_by_min_order_value(df):
    if(df['minOrderValue'] == 0): 
        return '#FFD3D5'
    elif(df['minOrderValue'] <= 10):
        return '#DE9FA2'
    elif(df['minOrderValue'] <= 20):
        return '#B86B6F'
    elif(df['minOrderValue'] <= 30):
        return '#CC323A'
    elif(df['minOrderValue'] <= 40):
        return '#97050C'
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
df = df.query('supports_delivery == True')

df['deliveryFeeDefault'] = df['deliveryFeeDefault']/100
df['minOrderValue'] = df['minOrderValue']/100
df['priceRange_0'] = df['priceRange_0']/100

df['location_lat']= df['location_lat'].astype(float)
df['location_lng']= df['location_lng'].astype(float)

df['colors'] = df.apply(categorize_colors_by_shipping_fee, axis = 1)

df.rename({'quantity':'distance'},axis=1,inplace=True)




x,y = df['location_lng'],df['location_lat']

colors = df['colors']
mycoordinates = list(zip([13.416735731033002,52.5111974101559]))

shape=gpd.read_file('C:/Users/Aakash Sharma/Downloads/berlin-latest-free/gis_osm_places_a_free_1.shp')
ax = shape.plot(figsize=(7,7),alpha=0.3,edgecolor='#032a69',color='#1f65d5')
ax.scatter(x,y,marker="o", color=colors, alpha=0.8, s = 10)
ax.scatter(mycoordinates[0],mycoordinates[1],color='red',s=40)

# coordinates range is set of points that we choose to create our polygon with.

coordinates_range = [(13.38,52.49), (13.36,52.495), (13.375,52.515) ,(13.37,52.523),(13.368,52.531)
,(13.381,52.552),(13.379,52.552),(13.417,52.554),(13.432,52.548),(13.45,52.528)
,(13.461,52.524),(13.467,52.517),(13.466,52.502),(13.462,52.494),(13.425,52.475),(13.40,52.485)]

polygon = mpatches.Polygon(coordinates_range, closed=True,alpha=0.5, color = 'red')
plt.gca().add_patch(polygon)


labels = ['0', '<=3.99', '<=4.99','> 4.99']
legend_colors = ['#e4dbdb','#ffc6a7','#fd6c1d','black']

handles = []

for i, color in enumerate(legend_colors):
    handle = mpatches.Patch(color=color, label=labels[i])
    handles.append(handle)

ax.legend(handles=handles)

ax.axis('off')




# Apply the function to each row and store the result in a new column
df['point'] = df.apply(create_point, axis=1)
df = df.drop(['isOpenForOrder', 'isOpenForPreorder'],axis=1)

gdf = gpd.GeoDataFrame(df, geometry="point")

polygon = Polygon(coordinates_range)
gdf['Function_check_range'] = gdf.apply(lambda row: inside_of_polygon(row['point'], polygon),axis=1)

gdf = gdf.drop(['location_lat','location_lng'],axis=1)




outside = gdf.query('deliveryFeeDefault <= 3.99 & Function_check_range == "Restaurant outside polygon"').select_dtypes(['int64','float64','bool'])
inside = gdf.query('Function_check_range == "Restaurant inside polygon"').select_dtypes(['int64','float64','bool'])



outside['bucket_fee'] = outside.apply(bucket_fee,axis=1)
inside['bucket_fee'] = inside.apply(bucket_fee,axis=1)



create_scatter_filter_query(shape, df, 'indicators_isDeliveryByScoober == True','indicators_isDeliveryByScoober == False')


fig, ((ax2, ax1),(ax4,ax3)) = plt.subplots(2, 2, figsize=(14,7))
ax1.set_title('Delivery Fee inside Polygon')
counts1 = inside['bucket_fee'].value_counts()
counts1 = counts1.reindex(['0', '<= 3.99', '<= 4.99','> 5.00'])
ax1.bar(counts1.index,counts1.values, color='red')

ax2.set_title('Delivery Fee outside Polygon')
counts2 = outside['bucket_fee'].value_counts()
counts2 = counts2.reindex(['0', '<= 3.99', '<= 4.99','> 5.00'])
ax2.bar(counts2.index,counts2.values)

ax3.set_title('Distance (m) Restaurant to Customer inside Polygon')
ax3.hist(inside['distance'], color='red')
ax4.set_title('Distance (m) Restaurant to Customer outside Polygon')
ax4.hist(outside['distance'])

plt.subplots_adjust(hspace=0.4)

plt.show()






convert_boolean_columns_to_float(outside)
convert_boolean_columns_to_float(inside)

outside_cols = outside[['indicators_isDeliveryByScoober','indicators_isNew','indicators_isSponsored','priceRange_0','popularity_0','minOrderValue']]
inside_cols = inside[['indicators_isDeliveryByScoober','indicators_isNew','indicators_isSponsored','priceRange_0','popularity_0','minOrderValue']]


fig,((ax1, ax2, ax7, ax8),(ax3,ax4, ax9, ax10),(ax5,ax6, ax11, ax12)) = plt.subplots(3, 4, figsize=(14,7))


fig.text(0.30, 0.95, 'Outside Polygon', ha='center', fontsize=15)
fig.text(0.7, 0.95, 'Inside Polygon', ha='center', fontsize=15)


ax1.set_title('isDeliveryByScoober')
ax1.hist(outside_cols['indicators_isDeliveryByScoober'])

ax2.set_title('isNew')
ax2.hist(outside_cols['indicators_isNew'])

ax3.set_title('isSponsored')
ax3.hist(outside_cols['indicators_isSponsored'])

ax4.set_title('priceRange')
ax4.hist(outside_cols['priceRange_0'])

ax5.set_title('popularity')
ax5.hist(outside_cols['popularity_0'])

ax6.set_title('minOrderValue')
ax6.hist(outside_cols['minOrderValue'])

ax7.set_title('isDeliveryByScoober')
ax7.hist(inside_cols['indicators_isDeliveryByScoober'], color='red')

ax8.set_title('isNew')
ax8.hist(inside_cols['indicators_isNew'], color='red')

ax9.set_title('isSponsored')
ax9.hist(inside_cols['indicators_isSponsored'], color='red')

ax10.set_title('priceRange')
ax10.hist(inside_cols['priceRange_0'], color='red')

ax11.set_title('popularity')
ax11.hist(inside_cols['popularity_0'], color='red')

ax12.set_title('minOrderValue')
ax12.hist(inside_cols['minOrderValue'], color='red')

plt.subplots_adjust(hspace=0.4)



create_scatter_filter_query(shape,df,'indicators_isDeliveryByScoober == True','indicators_isDeliveryByScoober == False')




df.query('indicators_isDeliveryByScoober == True').corr()['deliveryFeeDefault'].sort_values(ascending=False)[2:]

df.query('indicators_isDeliveryByScoober == False').corr()['deliveryFeeDefault'].sort_values(ascending=False)[2:]


df1 = df.query('indicators_isDeliveryByScoober == True')

df1['colors_min_order'] = df1.apply(categorize_colors_by_min_order_value,axis=1)

x,y = df1['location_lng'],df1['location_lat']
colors = df1['colors_min_order']

mycoordinates = list(zip([13.416735731033002,52.5111974101559]))

handles = []

labels = ['0', '<= 10', '<= 20','<= 30','<= 40', '> 40']
legend_colors = ['#FFD3D5','#DE9FA2','#B86B6F','#CC323A','#97050C','black']

for i, color in enumerate(legend_colors):
    handle = mpatches.Patch(color=color, label=labels[i])
    handles.append(handle)

fig,(ax1, ax2) = plt.subplots(1, 2, figsize=(14,7))

shape=gpd.read_file('C:/Users/Aakash Sharma/Downloads/berlin-latest-free/gis_osm_places_a_free_1.shp')
ax1 = shape.plot(ax= ax1,figsize=(7,5),alpha=0.3,edgecolor='#032a69',color='#1f65d5')
ax1.scatter(x,y,marker="o", color=colors, alpha=0.8, s = 10)
ax1.scatter(mycoordinates[0],mycoordinates[1],color='red',s=40)
ax1.legend(handles=handles)
ax1.axis('off')

df2 = df.query('indicators_isDeliveryByScoober == False')

df2['colors_min_order'] = df2.apply(categorize_colors_by_min_order_value,axis=1)

x,y = df2['location_lng'],df2['location_lat']
colors = df2['colors_min_order']

shape=gpd.read_file('C:/Users/Aakash Sharma/Downloads/berlin-latest-free/gis_osm_places_a_free_1.shp')
ax2 = shape.plot(ax= ax2,figsize=(7,5),alpha=0.3,edgecolor='#032a69',color='#1f65d5')
ax2.scatter(x,y,marker="o", color=colors, alpha=0.8, s = 10)
ax2.scatter(mycoordinates[0],mycoordinates[1],color='red',s=40)
ax2.legend(handles=handles)
ax2.axis('off')


fig.text(0.5, 0.9, 'Minimum Order Value', ha='center', fontsize=15)
fig.text(0.30, 0.8, 'indicators_isDeliveryByScoober == True', ha='center', fontsize=12)
fig.text(0.70, 0.8, 'indicators_isDeliveryByScoober == False', ha='center', fontsize=12)




df['bucket_fee'] = df.apply(bucket_fee,axis=1)
df['bucket_fee']



create_scatter_filter_query(shape,df,'indicators_isSponsored == True','indicators_isSponsored == False')




df1 = df[['distance','indicators_isDeliveryByScoober','indicators_isNew','indicators_isSponsored','priceRange_0','popularity_0','minOrderValue','deliveryFeeDefault']]
df2 = df[['distance','indicators_isDeliveryByScoober','indicators_isNew','indicators_isSponsored','priceRange_0','popularity_0','minOrderValue','deliveryFeeDefault']]


df1 = df1.query('indicators_isDeliveryByScoober == True')
df2 = df2.query('indicators_isDeliveryByScoober == False')


convert_boolean_columns_to_float(df1)
convert_boolean_columns_to_float(df2)


fig,((ax1, ax2, ax7, ax8),(ax3,ax4, ax9, ax10),(ax5,ax6, ax11, ax12),(ax13, ax14 ,ax15,ax16)) = plt.subplots(4, 4, figsize=(14,7))


fig.text(0.30, 0.95, 'Scoober Delivery', ha='center', fontsize=15)
fig.text(0.7, 0.95, 'No Scoober Delivery', ha='center', fontsize=15)


ax1.set_title('isDeliveryByScoober')
ax1.hist(df1['indicators_isDeliveryByScoober'])

ax2.set_title('isNew')
ax2.hist(df1['indicators_isNew'])

ax3.set_title('isSponsored')
ax3.hist(df1['indicators_isSponsored'])

ax4.set_title('priceRange')
ax4.hist(df1['priceRange_0'])

ax5.set_title('popularity')
ax5.hist(df1['popularity_0'])

ax6.set_title('minOrderValue')
ax6.hist(df1['minOrderValue'])

ax7.set_title('isDeliveryByScoober')
ax7.hist(df2['indicators_isDeliveryByScoober'], color='red')

ax8.set_title('isNew')
ax8.hist(df2['indicators_isNew'], color='red')

ax9.set_title('isSponsored')
ax9.hist(df2['indicators_isSponsored'], color='red')

ax10.set_title('priceRange')
ax10.hist(df2['priceRange_0'], color='red')

ax11.set_title('popularity')
ax11.hist(df2['popularity_0'], color='red')

ax12.set_title('minOrderValue')
ax12.hist(df2['minOrderValue'], color='red')

ax15.axis('off')
ax13.axis('off')



ax14.set_title('distance(m)')
ax14.hist(df1['distance'])


ax16.set_title('distance(m)')
ax16.hist(df2['distance'],color='red')


plt.subplots_adjust(hspace=0.6)



df1['bucket_fee']= df1.apply(bucket_fee,axis=1)
df2['bucket_fee']= df2.apply(bucket_fee,axis=1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8,2))

counts1 = df1['bucket_fee'].value_counts()
counts1 = counts1.reindex(['0', '<= 3.99', '<= 4.99','> 5.00'])
ax1.bar(counts1.index,counts1.values)
ax1.set_title('Delivery Fees with Scoober Delivery')


counts2 = df2['bucket_fee'].value_counts()
counts2 = counts2.reindex(['0', '<= 3.99', '<= 4.99','> 5.00'])
ax2.bar(counts2.index,counts2.values, color='red')
ax2.set_title('Delivery Fees w/o Scoober Delivery')
