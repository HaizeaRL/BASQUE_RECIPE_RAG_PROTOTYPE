# -*- coding: utf-8 -*-
"""
Created on Fri Mar  7 14:23:57 2025
GET RECIPES TABLE AND CORRECT DUPLICATES, ETC..
@author: USUARIO
"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import pandas as pd
import os
import itertools
import subprocess


def scrap_recipes_titles_and_url(sub_soup, base_url):
    
    recipes_list = []

    # Find all <h3> elements with text 'S'
    for h3 in sub_soup.find_all("h3", string="S"):
        # Find the next <ul> element after the <h3>
        ul = h3.find_next("ul")
        if ul:
            # Iterate over each <li> within the <ul>
            for li in ul.find_all("li"):
                # Find <a> tags with title starting with "Sukaldaritza liburua/Errezetak/"
                for link2 in li.find_all("a", attrs={"title": re.compile(r"^Sukaldaritza liburua/Errezetak/")}):
                    if link2:
                        # Get recipe title and URL
                        recipe_title = link2.text.split("/")[-1]
                        recipe_url = urljoin(base_url, link2.get("href"))
                        
                        # Add to dictionary
                        recipe_dict = {recipe_title: recipe_url}
                        
                        # Append to the list of recipes
                        recipes_list.append(recipe_dict)
    return recipes_list

def scrap_all_recipies(url, base_url):
    """
    Function that applies web scraping to find all basque recipies from url and retrieve recipes per
    ingredients.
    
    Parameters:
        url (str): The URL of the web page to scrape.
        base_url (str): The base URL of the web page to continue scrapping through sub links.

    Returns:
        list: A list of all ingredients found on the web page.
    """ 
    # Fetch the main page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Dictionary to store results
    ingredients_list = set()
    recipes =  {}

    # Find all <a> elements with title starting with "Kategoria:Osagaia:"
    for link in soup.find_all("a", attrs={"title": re.compile(r"^Kategoria:Osagaia:")}):
        # Get the href attribute to open the linked page   
        sub_url = link.get("href")  
        
        # get also de ingredient of the recipe and add to ingredients_list
        ingredient = link.text.split(":")[1]
        ingredients_list.add(link.text.split(":")[1])
        
        if sub_url:
            sub_response = requests.get(urljoin(base_url, sub_url))    
            sub_soup = BeautifulSoup(sub_response.text, "html.parser")    
        
            # obtain recipies title and urls by ingredients
            recipies_list = scrap_recipes_titles_and_url(sub_soup,base_url)
            
            # Group recipes by ingredient in a dictionary
            recipes[ingredient] = recipies_list

    # return actual ingredient list and recipes per ingredients
    return ingredients_list, recipes

def correct_capitalization(text):
    # Split the text into words
    words = text.split()
    
    # Make the first word capitalized and the rest in lowercase
    words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
    
    # Join the words back into a single string
    return words

def correct_text(text):

    # remove special characters
    text = text.replace('"', '').replace('“', '').replace(',', '').replace('-',' ').replace("'",'').replace('.jpg','').strip()

    # correct capitalization
    words = correct_capitalization(text)
    
    # correct numerization
    if words[len(words) - 1].isdigit():  
        words[len(words) - 2] = words[len(words) - 2]+words[len(words) - 1]
        words.pop()
    
    # Join the words back into a single string
    return ' '.join(words)


def recipe_dict_into_df(recipe_dict):
    # List to store the data
    data = []
    viewed_recipes = []

    # Loop through the dictionary and extract the necessary information
    for ingredient, recipe_list in recipe_dict.items():
        for recipe in recipe_list:
            # Assuming each recipe is a dictionary with a single key-value pair
            for title, url in recipe.items():  # Iterate over key-value pairs 
            
                # correct recipe title
                title = correct_text(title)                    
                            
                # Add each recipe to the data list with ingredient, title, and URL
                data.append({
                    "ingredient": ingredient,
                    "recipe": title,  # Extract the recipe title (key)
                    "order": None,  
                    "technique":  None,  
                    "origin":  None,  
                    "recipe_url": url       # Extract the recipe URL (value)
                })

    # Convert the list of dictionaries into a pandas DataFrame
    return pd.DataFrame(data)

def group_titles_with_ingredients(df):
    # Group by 'recipe' and aggregate:
    grouped_df = (df.groupby('recipe', as_index=False)
                    .agg({
                        "ingredient": lambda x: list(sorted(set(x.dropna()))),  # Unique sorted list without NaN
                        "order": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "technique": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "origin": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "recipe_url": list
                    }))
    return grouped_df

# get similar recipes by scapy
def get_recipe_pairs_to_compare(df):
    # obtain recipe_list from df
    recipe_list =  df["recipe"].tolist()
    
    # obtain recipe pairs
    return itertools.combinations(recipe_list, 2)

# Función para calcular la similitud entre frases
def calcular_similitud(frase1, frase2):
    # Procesar las frases con spaCy
    doc1 = nlp(frase1)
    doc2 = nlp(frase2)
    
    # Calcular la similitud entre las frases
    similitud = doc1.similarity(doc2)
    
    return similitud

def compare_recipe_words(recipe1, recipe2):
    
    # get words
    words1 = recipe1.split()
    words2 = recipe2.split()
    
    # Compare words len
    if len(words1) == len(words2):
        return True
    else:
        return False
    
def get_similar_recipe_pairs(recipe_pairs, threshold, save_path):
    
    for recipe1, recipe2 in recipe_pairs: 
        # calculate similarity
        similarity = calcular_similitud(recipe1, recipe2)
        
        # filter only those that superate threshold and have same words
        if similarity > threshold and compare_recipe_words(recipe1,recipe2):
            # Add result 
            data.append({
                "item1": recipe1,
                "item2": recipe2,  
                "equal":  None ,
                "incorrect":  None 
            })
            print(f"Pair: {recipe1} <-> {recipe2}")
            
    # create df 
    simil_df = pd.DataFrame(data)   
    # save in specific path
    simil_df.to_csv(os.path.join(save_path,"similarities.csv"), index= False)   
    return os.path.join(save_path,"similarities.csv")



def compare_recipes_by_scapy(url, whl_file, recipe_pairs, threshold, save_path):
   # download scapy model
   response = requests.get(url)
   
   # save in local
   with open(whl_file, 'wb') as f:
       f.write(response.content)
       
   # install
   subprocess.check_call([os.sys.executable, '-m', 'pip', 'install', whl_file])

   # load
   nlp = spacy.load('es_core_news_sm')
   
   # get similar recipes list to correct by user
   file_path = get_similar_recipe_pairs(recipe_pairs, threshold, save_path)
   print(f"\tPlease check and mark titles to remove, in: {file_path}")
   return file_path

# obtain recipe base table
base_url = "https://eu.wikibooks.org/wiki/"
url = urljoin(base_url, "Sukaldaritza_liburua/Azala")
print(f"STEP1: APPLYING WEB SCRAPPING TO OBTAIN RECIPE LIST: {url} ...")
ingredients_list, recipe_dict = scrap_all_recipies(url, base_url)
recipes_df = recipe_dict_into_df(recipe_dict)
print(f"RECIPES TABLE OBTAINED.")


# group ingredients by recipes
recipe_df_grouped = group_titles_with_ingredients(recipes_df)
print(f"RECIPES GROUPED BY INGREDIENTS.")


# get similar recipes list to correct by user
recipe_pairs = get_recipe_pairs_to_compare(recipe_df_grouped)  
save_path = ""
file_path = compare_recipes_by_scapy(url, whl_file, recipe_pairs, threshold, save_path)
print(f"RECIPES TITLES CLASSIFIED BY SIMILARITY.")





# URL del archivo .whl
url = 'https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.8.0/es_core_news_sm-3.8.0-py3-none-any.whl'

# Ruta donde se descargará el archivo .whl
whl_file = 'es_core_news_sm-3.8.0-py3-none-any.whl'













# Descargar el archivo .whl
print("Descargando el archivo .whl...")
response = requests.get(url)

# Guardar el archivo en el directorio actual
with open(whl_file, 'wb') as f:
    f.write(response.content)

print(f"Archivo descargado: {whl_file}")

# Instalar el archivo .whl usando pip
print("Instalando el modelo...")
subprocess.check_call([os.sys.executable, '-m', 'pip', 'install', whl_file])


nlp = spacy.load('es_core_news_sm')

# Verificar si el modelo se cargó correctamente
print("Modelo cargado correctamente.")



a = "es_core_news_sm-3.8.0-py3-none-any.whl"

a.split("-")[0]

    

# Open a file in write mode

data = []
for frase1, frase2 in pares_de_frases:    
    similitud = calcular_similitud(frase1, frase2)
    #print(f"Similitud entre '{frase1}' y '{frase2}': {similitud:.2f}")
    
    # Decidir si son similares según un umbral de similitud (ej. 0.7)
    if similitud > 0.9 and comparar_numero_palabras(frase1,frase2):
        # Add each recipe to the data list with ingredient, title, and URL
        data.append({
            "item1": frase1,
            "item2": frase2,  
            "equal":  None ,
            "correct":  None 
        })
        print(f"Pair: {frase1} <-> {frase2}")
        
simil_df = pd.DataFrame(data)   
simil_df.to_csv(os.path.join(out_url,"similitudes.csv"), index= False)    
print("END")
  