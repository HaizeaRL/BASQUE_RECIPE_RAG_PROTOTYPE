# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 10:09:33 2025
OBTAIN DATA BASE DATA BY WEB SCRAPPING.
    - Recipes by technique
@author: hrumayor
"""


import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin



def scrap_recipes_titles(sub_soup):
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
                        
                        # add recipe to list
                        recipes_list.append(recipe_title)
    return recipes_list


def scrap_recipes_by_category_list(url, base_url , category_list): 
    # Fetch the main page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Dictionary to store results
    response_dictionary = {}
     

    # Find all <a> elements with title starting with category_list elements
    for link in soup.find_all("a", href=True):
        if link.get('title') in category_list:
            key = link.text
            sub_url = link.get("href") 
            if sub_url:
                sub_response = requests.get(urljoin(base_url, sub_url))    
                sub_soup = BeautifulSoup(sub_response.text, "html.parser")    
            
                # obtain recipe titles list
                recipes_list = scrap_recipes_titles(sub_soup)
                # save in the dictionary
                response_dictionary[key] = recipes_list      

    return response_dictionary

#  call to function
base_url = "https://eu.wikibooks.org/wiki/"
url = urljoin(base_url, "Sukaldaritza_liburua/Azala")

techniques = ["Kategoria:Carpaccio", "Kategoria:Egosi", "Kategoria:Entsalada",
            "Kategoria:Erre", "Kategoria:Erregosi", "Kategoria:Frijitu", 
            "Kategoria:Ketu","Kategoria:Konfitatu", "Kategoria:Kremak", "Kategoria:Labekatu",
            "Kategoria:Marian", "Kategoria:Plantxan", "Kategoria:Sueztitu", "Kategoria:Zopak"]

techniques_dict = scrap_recipes_by_category_list(url, base_url,techniques)

# VISUALIZE RESULT
for key in techniques_dict.keys():
    print("\n\n",key.upper())
    for recipe in techniques_dict.get(key):
        print("- ", recipe)
