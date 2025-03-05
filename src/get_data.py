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
#print("Shape df: ", recipe_df.shape)

# GROUP RECIPES BY INGREDIENTS
recipe_df_grouped = wsf.group_titles_with_ingredients(recipe_df)
'''for index, row in recipe_df_grouped.iterrows():    
    print(f"RECIPE: {row['Title']} INGREDIENTS: {row['Ingredient']}, ORDER: {row['Order']}, TECH: {row['Technique']}")
print("Shape df: ", recipe_df_grouped.shape)'''

# FIX RECIPE TITLE FROM DF '“ Tomate nahaskia'
for index, row in recipe_df_grouped.iterrows():
    if '“ ' in row['Title']:
        # correct recipe_df value
        aux = row['Title']
        row['Title'] = aux.replace('“ ',"")


# COMPLETE DATA: ADD DISH_ORDER TO EMPTY RECIPES BY LOGIC
no_order = wsf.complete_dish_order(recipe_df_grouped)
if len(no_order) >0:
    print("Recipes without dish order: ", len(no_order))

# ASK USER TO COMPLETE THOSE RECIPES WITHOUT DISH ORDER
wsf.complete_dish_order_by_user(recipe_df_grouped, no_order)

# validate result, NO RECIPE WITHOUT DISH ORDER
no_order = wsf.complete_dish_order(recipe_df_grouped)
if len(no_order) >0:
    print("Recipes without dish order")
    for recipe in no_order:
        print("- ", recipe)
else:
    print("There is no recipes without dish order")

# SAVE RECIPES TABLE UNTIL NOW
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_folder = os.path.join(project_root, 'data')

# Ensure the 'data' folder exists
os.makedirs(data_folder, exist_ok=True)
recipe_df_grouped.to_csv(os.path.join(data_folder, "recipes.csv"), index = False)


'''# RECIPES BY DISH ORDER
wsf.ask_for_recipes_by_order(recipe_df)'''


