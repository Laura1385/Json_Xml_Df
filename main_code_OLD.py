#Install all the libraries the project needs
#pip install -r requirements.txt 

import json #for PUNTO A
import pandas as pd #for PUNTO A

#pip install nltk #for PUNTO C
import nltk #for PUNTO C
nltk.download('punkt') #for PUNTO C
from nltk.tokenize import word_tokenize

#pip install pymongo #for PUNTO D2
import pymongo #for PUNTO D2



import warnings #only for os
warnings.filterwarnings("ignore") #only for os

#------------------------------------

#PUNTO A
#Fetch/retrive data JSON

name_json='jsondata.json'

#Def that reads a JSON file and transforms it into a df by tagging columns
def jsonfile(name_json):
    #Read and transform into a dictionary
    with open(name_json) as f:
        data = json.load(f)

    #pd.json_normalize convert the JSON into a DataFrame
    df = pd.json_normalize(data)

    #Rename columns using dictionary keys
    for col in df.columns:
        df.rename(columns={col: col}, inplace=True)  

    return df

#------------------------------------

#PUNTO B
#Store Data into a structure

#Calling the json_to_dataframe function and printing the result
df = jsonfile(name_json)
print(df.head(3))

#Export to Excel
df.to_excel('Dirty_JSON.xlsx', index=False) 
print("\n\n File: Dirty_JSON.xlsx exported!")

#------------------------------------

#PUNTO C
#Transform data - CLEANING (!@#$luca1984.!@# => luca)

#Check column type
print(df.dtypes,'\n\n')

#Converts all df's values to lower case, if the type's columns is object
df_low = df.apply(lambda x: x.str.lower() if(x.dtype == 'object') else x)

#Change '@' & '.' in '_'
df_low['email'] = df_low['email'].str.replace(r'[@]', '_', regex=True)
df_low['ip_address'] = df_low['ip_address'].str.replace(r'[.]', ' ', regex=True)

#Delete chars from 'only_digit' 
df_low['only_digit'] = df_low['only_digit'].str.replace('[a-zA-Z]', '', regex=True)

#Delete numbers from 'only_char' 
df_low['only_char'] = df_low['only_char'].str.replace('\d+', '', regex=True)

#Delete coloum 'json' 
df_low.drop(columns=['json'], inplace=True)

print("Df after creansing:\n", (df_low.head(3)))

#------------------------------------

#PUNTO C
#Transform data - TOKENIZATION/SPLITTING (xxx|yyy_zzz => xxx yyy zzz)

#Creation of 3 new coloumns with 'mail' values 
df_low2 = df_low.assign(email_name = df_low.email)
df_low3 = df_low2.assign(email_service = df_low2.email)
df_low4 = df_low3.assign(email_extens = df_low3.email)


#Splitting of email value 
df_low4['email_name'] = df_low4['email_name'].str.split('[-_\.]',expand = True,regex = True)[0]
df_low4['email_service'] = df_low4['email_service'].str.split('[-_\.]',expand = True,regex = True)[1]
df_low4['email_extens'] = df_low4['email_extens'].str.extract(r'[^_.]*(\..*)')

#Check duplicates
dup_df = df_low4[df_low4.duplicated()]

if dup_df.empty:
    print('No duplicates ;) \n\n')
else:
    print(dup_df)


print("Df after Tokenization/Splitting:\n", (df_low4.head(3)))

#------------------------------------

#PUNTO C
#Transform data - NORMALIZATION  (nlp library)
#pip install nltk

import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize

#Apply() applica la tokenizzazione alle celle della colonna 'email'. 
#Lambda prende i valori della colonna 'email' (x) e applica la funzione word_tokenize() per suddividere in token (parole). 
#I token vengono salvati nella nuova colonna 'email_tokens' nel df.
df_low4['email_tokens'] = df['email'].apply(lambda x: word_tokenize(x))

print("Df after Normalization:\n", (df_low4.head(3)))

#------------------------------------

#PUNTO D1
#Create a New file
   
#Export to Excel
df_low4.to_excel('Final_JSON.xlsx', index=False) 
print("\n\n File: Final_JSON.xlsx exported!")

#------------------------------------

#PUNTO D2
#Store data into DB MONGO
#https://stackoverflow.com/questions/20167194/insert-a-pandas-dataframe-into-mongodb-using-pymongo

#pip install pymongo
import pymongo

myclient1 = pymongo.MongoClient("mongodb://localhost:27017/")
mydb1 = myclient1["Database_Json"]
mycol1 = mydb1["df_low4"]

df = df_low4
fields = df.to_dict('records')
mycol1.insert_many(fields) 

print("\n\n Df exported to MongoDB!")
