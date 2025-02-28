# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 12:28:25 2025

@author: hrumayor
"""

import requests
from bs4 import BeautifulSoup
import re

def scrape_ingredients(url):
    """
    Function that applies web scraping to find and retrieve recipe ingredients.
    
    Parameters:
        url (str): The URL of the web page to scrape.

    Returns:
        list: A list of all ingredients found on the web page.
    """ 
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    ingredients = set()

    # Find all <a> elements where the title starts with "Kategoria:Osagaia:"
    for link in soup.find_all("a", attrs={"title": re.compile(r"^Kategoria:Osagaia:")}):
        if link:
            ingredient = link.text.split(":")[1]
            if ingredient:  
                ingredients.add(ingredient)  # Add ingredient name to the set       
            
    # Find all <hlist> elements where its list element <li> title is "Sukaldaritza liburua/Osagaiak/"
    for div_hlist in soup.find_all("div", class_="hlist"):
        if div_hlist:
           # Find all <ul> inside the div
           for ul in div_hlist.find_all("ul"):
               for li in ul.find_all("li"):
                   for link in li.find_all("a", attrs={"title": re.compile(r"^Sukaldaritza liburua/Osagaiak/")}):
                       if link:
                           ingredient = link.text.split(".")[0]
                           if ingredient and ingredient not in ingredients:  
                               ingredients.add(ingredient)  # Add ingredient name to the set
                         
    return list(ingredients)



def separate_conpound_ingredients(ingredient_list):
    """
    Function that separates compound ingredients by splitting each ingredient string on the delimiters "eta"  or "edo".
    Each component is stripped of whitespace and capitalized. Example: Perretxikoak eta onddoak is separated in 2 elements
    Perretxikoak, Onddoak.
    
    Parameters:
        ingredient_list (list): A list of ingredients.
    Returns:
        list: A deduplicated list of cleaned ingredient components.
    """     
    processed_ingredients = []
    
    for item in ingredient_list:
        # Split text by "eta" or "edo"
        parts = re.split(r'\s*(?:eta|edo|,)\s*', item)
        
        # strip and capitalize conpound ingrediens         
        cleaned_lists = [part.strip().capitalize() if len(part.strip()) > 1 else [""] for part in parts]
        processed_ingredients.extend(cleaned_lists)
    
    # remove duplicates
    return list(set(processed_ingredients))

def singularize(word):
    """
    Normalize a Basque word by singularizing it.

    Parameters:
        word (str): A word to singularize.

    Returns:
        str: The singularized form of the word.
    """
    if word.endswith("rrak"):
        # Example: "Itsas belarrak" -> "Itsas belar"
        return word[:-3]
    elif word.endswith("iak"):
        # Example: "Esnekiak" -> "Esneki"
        return word[:-3] + "i"
    elif word.endswith("oak"):
        # Example: "Onddoak" -> "Onddo"        
        return word[:-2]
    elif word.endswith("oa"):
        # Example: "Bakailaoa" -> "Bakailao"        
        return word[:-1]
    elif word.endswith("eak"):
        # Example: "Lekaleak" -> "Lekale"
        return word[:-2]
    elif word.endswith("ia"):
        # Example: "Legamia" -> "Legami"
        return word[:-1]
    elif word.endswith("k"):
        # Example: "Pasak" -> "Pasa"
        return word[:-1]
    elif word.endswith("na"):
        # Example: "Arraina" -> "Arrain"
        return word[:-1]
    else:
        return word


def get_singularized_list(word_list):
    """
    Normalize a list of Basque words by singularizing each one.

    Parameters:
        word_list (list of str): A list of words to normalize.

    Returns:
        list: A list of singularized words.
    """
    # Use a set to avoid duplicate singularized words, then convert to list
    singularized_set = {singularize(word) for word in word_list}
    return list(singularized_set)



# get ingredients list
ingredient_list = scrape_ingredients("https://eu.wikibooks.org/wiki/Sukaldaritza_liburua/Azala")

# clean and normalize ingredients
cleaned_list = separate_conpound_ingredients(ingredient_list)
print(f"Ingredients ({len(cleaned_list)}) , separated list {cleaned_list}")

singularized_list = get_singularized_list(cleaned_list)
print(f"\nIngredients ({len(singularized_list)}) , normalized list {singularized_list}")


import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin




# URL of the main page to start from
url = "https://eu.wikibooks.org/wiki/Sukaldaritza_liburua/Azala"
base_url ="https://eu.wikibooks.org/"

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
       
        recipies_list = []
        
                
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
                            recipe_url = link2.get("href")
                            
                            # Add to dictionary
                            recipe_dict = {recipe_title: recipe_url}
                            
                            # Append to the list of recipes
                            recipies_list.append(recipe_dict)
        
        # Group recipes by ingredient in a dictionary
        recipes[ingredient] = recipies_list
        
        
        
def complete_ingredients_subgroups_techniques(stop_words_url, ingredients_list):
    subgroups_dict_list = set()
    technique_list = set()
 
    # Fetch the stop words
    response = requests.get(stop_words_url)
    stop_words = set(response.text.splitlines())

    for key in recipes.keys():
        print("\nRecipies of:", key)
        views = set()
        for recipe_list in recipes.get(key):
            for recipe in recipe_list:
                # Your list of words
                words = recipe.split(" ")

                # Filter out stop words
                filtered_words = [word for word in words if word.lower() not in stop_words]
                
                for word in filtered_words:
                    if word not in views:
                        views.add(word)
                        while True:
                            print("---------")
                            n = input(f"Is the word '{word}' subgroup of ingredient '{key}'? (y/n): ").strip().lower()
                            if n == 'y':
                                subgroups_dict_list.add((key, word))
                                break
                            elif n == 'n':
                                while True:
                                    n = input(f"Is the word '{word}' an ingredient? (y/n): ").strip().lower()
                                    if n == 'y':
                                        ingredients_list.add(word)
                                        break
                                    elif n == 'n':
                                        while True:
                                            n = input(f"Is the word '{word}' a technique? (y/n): ").strip().lower()
                                            if n == 'y':
                                                technique_list.add(word)
                                                break
                                            elif n == 'n':
                                                break
                                            else:
                                                print("Invalid input. Please enter 'y' or 'n'.")
                                                continue
                                        break
                                    else:
                                        print("Invalid input. Please enter 'y' or 'n'.")
                                        continue
                                break
                            else:
                                print("Invalid input. Please enter 'y' or 'n'.")
                                continue



def conplet_ingredients(recipes):
    for key in recipes.keys():
        print("\nRecipies of:", key)
        views = set()
        for recipe_list in recipes.get(key):
            for recipe in recipe_list:
                # Your list of words
                words = recipe.split(" ")
                for word in words:
                    if word not in views:
                        views.add(word)
                        print("---------")
                        while True:
                            n = input(f"Is the word '{word}' an ingredient? (y/n): ").strip().lower()
                            if n in ('y', 'n'):
                                break
                            print("Invalid input. Please enter 'y' or 'n'.")
                            
                            if n == 'y':
                                ingredients_list.add(word)
                                ingredients_list
                                
        

                