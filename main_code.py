#From Json e XML to df, cleansing and from df to Database

#Install all the libraries the project needs
#pip install -r requirements.txt 

import os
import json #Point A_JSON
import xml.etree.ElementTree as ET #Point A_XML
import pandas as pd #Point B
import nltk #Point C Normalizzation
nltk.download('punkt') #Point C Normalizzation
from nltk.tokenize import word_tokenize #Point C Normalizzation
import pymongo #Point D2_Mongo

import warnings #only for os
warnings.filterwarnings("ignore") #only for os

#------------------------------------------------------------------------------------------

#POINT A
#--> Retrives data JSON

name_json='Input/jsondata.json'
#DEF that reads a JSON file and transforms it into a df by tagging columns
def jsonfile(name_json):
    #Reads and transforms into a dictionary
    with open(name_json) as f:
        data = json.load(f)

    #Point B 
    #Stores Data into a structure 
    #pd.json_normalize converts the JSON into a DataFrame
    df = pd.json_normalize(data)

    return df

#Calls the jsonfile function and prints the result
df_j = jsonfile(name_json)
#print(df_j.head(3))

#Deletes empty coloumns 
df_j.drop(columns=['json'], inplace=True)
print(df_j.head(3))

#Export to Excel
df_j.to_excel('Dirty_JSON.xlsx', index=False) 
print("\n\nFile: Dirty_JSON.xlsx exported!")


#--> Retrives data XML

name_xml='Input/dataset.xml'
#DEF that reads a XML file and transforms it into a df by tagging columns
def xml(name_xml):
    tree = ET.parse(name_xml)
    #Reads xml file and returns the object of typ
    #(the hierarchical structure of the XML tree)
  
    root = tree.getroot()
    #Obtains the root node of the object tree
    #(the starting point for navigating within the XML structure)

    tag=[] #Empty array/list
    #Populates the array/list and deletes duplicate values 
    #(SET is dangerous because even if it cleans up duplicates, it messes up the order of the elements!!!)
    for elem in root.iter():
        if elem.tag not in tag: 
            tag.append(elem.tag)

    #Creates column header with tags and an empty df
    heading = list(tag)
    df = pd.DataFrame(columns=heading)

    rows_data = []
    #Iterates on XML elements and populates the DataFrame
    for elem in root.iter():
        data = {}
        for tag in heading:
            if elem.find(tag) is not None:
                data[tag] = elem.find(tag).text
            else:
                data[tag] = None
        #Adds the row data dictionary to the list of rows
        rows_data.append(data)

    #Point B 
    #Stores Data into a structure 
    #Creates a new DataFrame from the rows
    df = pd.DataFrame(rows_data)

    #Deletes empty rows from id coloumn
    df.dropna(subset=['id'], inplace=True)

    #Deletes empty coloumns 
    df.drop(columns=['dataset', 'json','record'], inplace=True)

    return df

#Calls the xml function and prints the result
df_x = xml(name_xml)
#sorted_dfxml = df_x.sort_values(by=['last_name'], ascending=False) #Sorted by last_name
print(df_x.head(3))

#Export to Excel
df_x.to_excel('Dirty_XML.xlsx', index=False) 
print("\n\nFile: Dirty_XML.xlsx exported!")

#------------------------------------------------------------------------------------------

#POINT C
#--> Transforms data - CLEANING (!@#$luca1984.!@# => luca)

#JSON
#DEF that does several cleaning 
dfc = df_j.copy()
ty = 'JSON'
def clng(dfc, ty):
    #Checks column type
    print(f'\nThe coloumns of df from Input {ty} are:\n',dfc.dtypes,'\n')

    #Converts all df's values to lower case, if the type's columns is object
    df_low = dfc.apply(lambda x: x.str.lower() if(x.dtype == 'object') else x)
    
    #Change '@' & '.' in '_'
    df_low['email'] = df_low['email'].str.replace(r'[@]', '_', regex=True)
    df_low['ip_address'] = df_low['ip_address'].str.replace(r'[.]', ' ', regex=True)

    #Deletes chars from 'only_digit' 
    df_low['only_digit'] = df_low['only_digit'].str.replace('[a-zA-Z]', '', regex=True)

    #Deletes numbers from 'only_char' 
    df_low['only_char'] = df_low['only_char'].str.replace('\d+', '', regex=True)

    print(f"\nDf {ty} after creansing:\n", (df_low.head(1)))

    return df_low

#Calls the DEF clng on JSON
df_jcln = clng(dfc,ty)

#XML
#Using the DEF clng on XML 
dfc = df_x.copy()
ty ='XML'
df_xcln = clng(dfc,ty)

#--> Transforms data - TOKENIZATION/SPLITTING (xxx|yyy_zzz => xxx yyy zzz)

#JSON
#DEF that splitting email's values 
dfc = df_jcln.copy()
ty = 'JSON'
def splt(dfc, ty):
    #Creations of 3 new coloumns with 'mail' values 
    df_low = dfc.assign(email_name = dfc.email)
    df_low0 = df_low.assign(email_service = df_low.email)
    df_low1 = df_low0.assign(email_extens = df_low0.email)

    #Splitting email's value 
    df_low1['email_name'] = df_low1['email_name'].str.split('[-_\.]',expand = True,regex = True)[0]
    df_low1['email_service'] = df_low1['email_service'].str.split('[-_\.]',expand = True,regex = True)[1]
    df_low1['email_extens'] = df_low1['email_extens'].str.extract(r'[^_.]*(\..*)')

    #Checks duplicates
    dup_df = df_low1[df_low1.duplicated()]

    if dup_df.empty:
        print(f'\n\nNo duplicates {ty} ;) \n')
        print(f"Df {ty} after Tokenization/Splitting:\n", (df_low1.head(1)))
    else:
        print(dup_df)
        
    return df_low1

#Calls the DEF splt on JSON
df_jsplt = splt(dfc, ty)

#XML
#Using the DEF splt XML
dfc = df_xcln.copy()
ty = 'XML'
df_xsplt = splt(dfc, ty)

#--> Transforms data - NORMALIZATION (nlp library)
#pip install nltk

#Apply() applies tokenization to the cells in the 'email' column. 
#Lambda takes the values from the 'email' column (x) and applies the word_tokenize() function to tokenize the tokens (words). 
#The tokens are saved in the new column 'email_tokens' in the df.

#JSON
#DEF that applies the normalizzation to email's
dfc = df_jsplt.copy()
ty = 'JSON'
old_df = df_j
def norm(dfc, ty, old_df):
    dfc['email_tokens'] = old_df['email'].apply(lambda x: word_tokenize(x)) #Take the first df created for have the entire mail adress
    print(f"\nDf {ty} after Normalization:\n", (dfc.head(3)))

    return dfc

#Calls the DEF norm on JSON
df_jnorm = norm(dfc, ty, old_df)

#XML
#Using the DEF norm on XML
dfc = df_xsplt.copy()
ty = 'XML'
old_df = df_x

df_xnorm = norm(dfc, ty, old_df)

#------------------------------------------------------------------------------------------

#Point D1
#Creates a New file

df_jnorm.to_excel('Final_df_JSON.xlsx', index=False) 
df_xnorm.to_excel('Final_df_XML.xlsx', index=False) 

print("\n'Final_df_JSON.xlsx' and 'Final_df_XML.xlsx' exported!")

#Chose if you want delete 'Dirty' files
response = input("\nDo you want to delete Dirty_JSON.xlsx e Dirty_XML.xlsx ? (y/n): ")
response_lower = response.lower() #Conver in lower case

if response_lower == 'y':
    try:
        os.remove('Dirty_JSON.xlsx')
        os.remove('Dirty_XML.xlsx')
        print("\n\nDone! File Dirty_JSON.xlsx and e Dirty_XML deleted\n")
    except FileNotFoundError:
        print("\nHey! There isn't any 'dirty' files!'-_- \n")
else:  
        print("\n\nOk, 'dirty' files not deleted.\n")


#Point D2
#Store data into DB MONGO
#https://stackoverflow.com/questions/20167194/insert-a-pandas-dataframe-into-mongodb-using-pymongo

#pip install pymongo

#DEF that stores JSON df in Mongo DB
db_name = "Database_Json"
db_collection = "df_jexp"
dfc = df_jnorm.copy()
ty = 'JSON'

def mongo (db_name, db_collection, dfc, ty):
    myclient1 = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb1 = myclient1[db_name]
    mycol1 = mydb1[db_collection]

    df = dfc
    fields = df.to_dict('records')
    mycol1.insert_many(fields) 

    print(f"\nDataframe {ty} exported to MongoDB!")

#Calls the DEF mongo on JSON
mongo_j = mongo (db_name, db_collection, dfc, ty)

#XML
#Using the DEF mongo on XML
db_name = "Database_XML"
db_collection = "df_xexp"
dfc = df_xnorm.copy()
ty = 'XML'

mongo_x = mongo (db_name, db_collection, dfc, ty)