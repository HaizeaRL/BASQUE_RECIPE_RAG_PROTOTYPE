import os
import sys
from urllib.parse import urljoin


# Add the parent directory (where modules is located) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import web_scrapping_functions as wsf

# WEB SCRAP: obtain ingredients and recipe list per ingredients with its url
base_url = "https://eu.wikibooks.org/wiki/"
url = urljoin(base_url, "Sukaldaritza_liburua/Azala")
ingredients_list, recipes = wsf.scrap_all_recipies(url, base_url)

# WEB SCRAP: obtain techniques - recipes relation
techniques = ["Kategoria:Carpaccio", "Kategoria:Egosi", "Kategoria:Entsalada",
            "Kategoria:Erre", "Kategoria:Erregosi", "Kategoria:Frijitu", 
            "Kategoria:Ketu","Kategoria:Konfitatu", "Kategoria:Kremak", "Kategoria:Labekatu",
            "Kategoria:Marian", "Kategoria:Plantxan", "Kategoria:Sueztitu", "Kategoria:Zopak"]
techniques_dict = wsf.scrap_recipes_by_category_list(url, base_url,techniques)

# WEB SCRAP: obtain dish_order - recipes relation
dish_order_categories = ["Kategoria:Lehen platerak","Kategoria:Bigarren platerak", 
                         "Kategoria:Azkenburukoak"]
order_dict = wsf.scrap_recipes_by_category_list(url, base_url,dish_order_categories)

# DATA JOIN: RELATE INGREDIENT BASED RECIPES WITH TECHNIQUE AND DISH ORDER
recipe_df = wsf.recipes_dict_to_df(recipes, techniques_dict , order_dict)

# COMPLETE DATA: ADD DISH_ORDER TO EMPTY RECIPES BY LOGIC
no_order = wsf.complete_dish_order(recipe_df)
if len(no_order) >0:
    print("Recipes without dish order")
    for recipe in no_order:
        print("- ", recipe)

# FIX RECIPE TITLE FROM DF '“ Tomate nahaskia'
for index, row in recipe_df.iterrows():
    if '“ ' in row['Title']:
        # correct recipe_df value
        aux = row['Title']
        row['Title'] = aux.replace('“ ',"")

# FIX FROM NO_ORDER LIST
no_order = [item.replace('“ ', "") if '“ ' in item else item for item in no_order]
if len(no_order) >0:
    print("\nRecipes without dish order (corrected)")
    for recipe in no_order:
        print("- ", recipe)

# ASK USER TO COMPLETE THOSE RECIPES WITHOUT DISH ORDER
wsf.complete_dish_order_by_user(recipe_df, no_order)

# validate result, NO RECIPE WITHOUT DISH ORDER
no_order = wsf.complete_dish_order(recipe_df)
if len(no_order) >0:
    print("Recipes without dish order")
    for recipe in no_order:
        print("- ", recipe)

# RECIPES BY DISH ORDER
wsf.ask_for_recipes_by_order(recipe_df)


