import os
import sys
from urllib.parse import urljoin

# Add the parent directory (where modules is located) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import web_scrapping_functions as wsf










# scrape recipies to get main ingredients and recipies according to those ingredients
base_url = "https://eu.wikibooks.org/wiki/"
url = urljoin(base_url, "Sukaldaritza_liburua/Azala")
ingredient_list, recipes = wsf.scrap_all_recipies(url, base_url)

# print first ingredient_list
print(f"Ingredients ({len(ingredient_list)}) \n {ingredient_list}")

# print relates recipies of ingredients
'''for key in recipes.keys():
    print("\nRecipies of:", key)
    for recipe_list in recipes.get(key):
        for recipe in recipe_list:
            print("- ", recipe)'''


# complete data with user answers
stop_words_url = "https://raw.githubusercontent.com/stopwords-iso/stopwords-eu/master/stopwords-eu.txt"
subgroups, ingredients_list, tech_list = wsf.ask_user_to_complete_data(stop_words_url, ingredient_list, recipes)

# Specify the file path
print("Subgroups: ",subgroups)
print("\nIngredients: ",ingredients_list)
print("\nTechniques: ",tech_list)

# ingredients subgroup

# clean and normalize ingredients subgroups

# get recipes and group for ingredient subgroup and techniques