# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 10:09:33 2025
OBTAIN DATA BASE DATA BY WEB SCRAPPING.
    -Ingredients and recipes
@author: hrumayor
"""


import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin


def scrap_recipes_titles_and_url(sub_soup):
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
            recipies_list = scrap_recipes_titles_and_url(sub_soup)
            
            # Group recipes by ingredient in a dictionary
            recipes[ingredient] = recipies_list

    # return actual ingredient list and recipes per ingredients
    return ingredients_list, recipes

# OBTAIN INGREDIENTS AND RECIPES
base_url = "https://eu.wikibooks.org/wiki/"
url = urljoin(base_url, "Sukaldaritza_liburua/Azala")
ingredients_list, recipes = scrap_all_recipies(url, base_url)
 
# VISUALIZE INGREDIENTS
print(ingredients_list) 

# VISUALIZE RECIPES
for key in recipes.keys():
    print("\n\n",key.upper(), "ERREZETAK")
    for recipe_list in recipes.get(key):
        for recipe in recipe_list:
            print("- ", recipe)
            


