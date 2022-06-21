# Python program to read
# json file
    
import json
import pandas as pd
from time import sleep
  
# # Fitbit Sleep Parsing
# f = open('sleep.json')
# sleep_data = {}
# data = json.load(f)
# # print(type(data['sleep']))
# for i in data['sleep']:
#     for j in i.keys():
#         if j != 'levels':
#             sleep_data[j] = i[j] 

# df = pd.DataFrame([sleep_data])
# df.to_csv('sleep_data.csv')

# Fitbit activities parsing 
f = open('fitbit_activities.json')
activity_data = {}
data = json.load(f)
# print(len(data['activities']))
for i in data['activities']:
    for j in i.keys():
        activity_data[j] = i[j]
    print(activity_data)
    break

df = pd.DataFrame([activity_data])
df.to_csv('activity_data.csv')


  
# Closing file
f.close()