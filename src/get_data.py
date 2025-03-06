import os
import sys
from urllib.parse import urljoin
import yaml
from pathlib import Path


# Add the parent directory (where modules is located) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import web_scrapping_functions as wsf

# read config file
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conf = yaml.safe_load(Path(os.path.join(root_path,"config.yaml")).read_text())



# WEB SCRAP: obtain ingredients and recipe list per ingredients with its url
base_url = conf["BASE_URL"]
url = urljoin(base_url, conf["URL_COMPLEMENT"])
print(f"STEP1: APPLYING WEB SCRAPPING TO: {url} ...")
ingredients_list, recipes = wsf.scrap_all_recipies(url, base_url)
print(f"\tRECIPES BY INGREDIENTS OBTAINED. GROUPED IN TOTAL OF {len(ingredients_list)} INGREDIENTS.")

# WEB SCRAP: obtain techniques - recipes relation
techniques = [conf["CATEGORY_PREFIX"]+ item for item in conf["TECHNIQUES_CATEGORIES"]]
techniques_dict = wsf.scrap_recipes_by_category_list(url, base_url,techniques)
print(f"\tRECIPES BY COOK TECHNIQUES OBTAINED. GROUPED IN TOTAL OF {len(techniques_dict.keys())} COOK TECHNIQUES.")

# WEB SCRAP: obtain dish_order - recipes relation
dish_order_categories = [conf["CATEGORY_PREFIX"]+ item for item in conf["DISH_ORDER_CATEGORIES"]]
order_dict = wsf.scrap_recipes_by_category_list(url, base_url,dish_order_categories)
print(f"\tRECIPES BY DISH ORDER OBTAINED. GROUPED IN: {order_dict.keys()}.")
print("END OF THE WEB SCRAPPING.")

print("STEP2: JOIN AND PREPROCESS RECIPES")
# DATA JOIN: RELATE INGREDIENT BASED RECIPES WITH TECHNIQUE AND DISH ORDER
recipe_df = wsf.recipes_dict_to_df(recipes, techniques_dict , order_dict)
print("\tRECIPES JOINED IN A DATAFRAME. (Relate recipes with dish order and cook techniques).")

# GROUP RECIPES BY INGREDIENTS
recipe_df_grouped = wsf.group_titles_with_ingredients(recipe_df)
print("\tRECIPES GROUPED BY INGREDIENTS.")
'''for index, row in recipe_df_grouped.iterrows():    
    print(f"RECIPE: {row['Title']} INGREDIENTS: {row['Ingredient']}, ORDER: {row['Order']}, TECH: {row['Technique']}")
print("Shape df: ", recipe_df_grouped.shape)'''

# FIX RECIPE TITLES. Remove: commas, '“' , '"' and whitespaces
for index, row in recipe_df_grouped.iterrows():
    # Clean the Title column by removing unwanted characters and stripping whitespace
    recipe_df_grouped.at[index, 'Title'] = (
        row['Title'].replace('"', '').replace('“', '').replace(',', '').replace('-',' ').replace("'",'').replace('.jpg','').strip()
    )
print("\tRECIPES TITLES CORRECTED (without commas and weird characters).")


# COMPLETE DATA: ADD DISH_ORDER TO EMPTY RECIPES BY LOGIC & AND ASKING TO THE USER
print("STEP3: COMPLETE MISSING VALUES")
print("CHECKING DISH ORDER AND COMPLETING...")
recipe_df_new = wsf.complete_dish_order_by_synomims_and_user(recipe_df_grouped, conf)

print("CHECKING COOK TECHNIQUES AND COMPLETING BY SYNONYMS...")
no_tech, without_tech = wsf.count_empty_techniques(recipe_df_new)
if without_tech !=0:
    print(f"\tThere are {without_tech} recipes without cook technique. Let's try to complete with synonims...")
    recipe_df_new = wsf.complete_tech_by_synonims(recipe_df_new, conf)
    no_tech1, without_tech1 = wsf.count_empty_techniques(recipe_df_new)
    if without_tech1 !=0:
        print(f"\tAfter corrected with synonims are {without_tech1} recipes without cook technique.")

print("CHECKING IF RECIPES CAN BE CLASSIFIED BY ORIGINS...")
recipe_df_new = wsf.complete_origin(recipe_df_new, conf)
no_tech_orig, without_tech_orig = wsf.count_empty_tech_and_origin(recipe_df_new)
if without_tech !=0:
    print(f"\tThere are {without_tech_orig} recipes without cook technique and origin.")   

print("CHECK RECIPES BY DISH_ORDER")
ord = conf["DISH_ORDER_CATEGORIES"]
wsf.get_recipes_by_category(recipe_df_new, ord, "Order")
print("---")

print("CHECK RECIPES BY TECHNIQUE")
tech = conf["TECHNIQUES_CATEGORIES"] + ["Betea", "Hotza"]
wsf.get_recipes_by_category(recipe_df_new, tech, "Technique")
print("---")

print("CHECK RECIPES BY ORIGIN")
orig = ["Italia", "Asia","Frantzia", "Europa","Mexiko", "Afrika", "Espainia","Bertakoa"]
wsf.get_recipes_by_category(recipe_df_new, orig, "Origin")
print("---")

# SAVE RECIPES TABLE UNTIL NOW.  Ensure the 'data' folder exists
data_folder = os.path.join(root_path, conf["DATA_PATH"])
os.makedirs(data_folder, exist_ok=True)

# save
recipe_df_new.to_csv(os.path.join(data_folder, conf["RECIPES_FILE_NAME"]), index = False)
print(f"\nSTEP5: RECIPE TABLE CORRECTLY SAVED IN: {os.path.join(data_folder, conf['RECIPES_FILE_NAME'])}")




'''TODO CORRECT FROM ENTSALADA
-  Legatz arrautzaztatua
-  Legatz betea
-  Legatz kokotea labean
-  Legatz kokotxak arrautzaztatuak
-  Legatza kokotea
-  Legatza otarrainxka saldarekin eta txirlekin
-  Legatza saltsa berdean txirla eta kokotxekin

TODO Remove duplicate recipes.
'''