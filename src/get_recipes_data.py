import os
import sys
from urllib.parse import urljoin
import yaml
from pathlib import Path


# Add the parent directory (where modules is located) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import get_data_functions as gdf

# Read config file
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conf = yaml.safe_load(Path(os.path.join(root_path, "config.yaml")).read_text(encoding="utf-8"))

# Create temporal data folder
data_tmp_folder = os.path.join(root_path, conf["TEMPORAL_DATA_PATH"])
os.makedirs(data_tmp_folder, exist_ok=True)

# Create data folder
data_folder = os.path.join(root_path, conf["DATA_PATH"])
os.makedirs(data_folder, exist_ok=True)

# Define web scrapping urls
base_url = conf["BASE_URL"]
url = urljoin(base_url, conf["URL_COMPLEMENT"])

# STEP1: WEBSCRAP DATA save dicts to define actions to take.
# INGREDIENTS & RECIPES
print(f"STEP 1: APPLYING WEB SCRAPPING TO OBTAIN RECIPE BASE LIST: {url} ...")
ingredients_list, recipe_dict = gdf.scrap_all_recipies(url, base_url)

# RECIPES BY DISH_ORDER
# get recipes by dish_order
dish_order_categories = [conf["CATEGORY_PREFIX"]+ item for item in conf["DISH_ORDER_CATEGORIES"]]
order_dict = gdf.scrap_recipes_by_category_list(url, base_url, dish_order_categories)

# RECIPES BY COOK TECHNIQUE
# get techniques list
techniques = [conf["CATEGORY_PREFIX"]+ item for item in conf["TECHNIQUES_CATEGORIES"]]
techniques_dict = gdf.scrap_recipes_by_category_list(url, base_url, techniques)

# STEP2: JOIN ALL DATA INTO DF
print(f"STEP 2: JOINING ALL DATA INTO SINGLE TABLE.")
recipe_df = gdf.recipes_dict_to_df(recipe_dict, techniques_dict , order_dict)
recipe_base_path= os.path.join(data_tmp_folder, "recipe_base.csv")
recipe_df.to_csv(recipe_base_path, index = False)

# STEP3: CORRECT RECIPE TITLES, CORRECT RECIPE TITLES MISSPELLINGS
print(f"STEP 3: CORRECT RECIPE TITLES MISSPELLINGS.")

# FIX RECIPE TITLES. Remove unwanted characters, non-capitalized , digits joined
for index, row in recipe_df.iterrows():
    recipe_df.at[index, 'recipe_new'] = gdf.correct_recipe_titles(row['recipe'])

new_order = ["ingredient_group", "recipe","recipe_new","order", "technique", "url"]
recipe_new_ordered = recipe_df[new_order]
recipe_new = gdf.replace_words(recipe_new_ordered, "recipe_new", conf["DICT_TO_CHANGE"])

#save new data
recipe_base_corrected_path= os.path.join(data_tmp_folder, "recipe_titles_corrected.csv")
recipe_new.to_csv(recipe_base_corrected_path, index = False)

# STEP4: GROUP RECIPES BY INGREDIENTS
print(f"STEP 4: GROUP RECIPES BY INGREDIENTS.")
recipes_group = gdf.group_titles_with_ingredients(recipe_new)

# STEP5: REMOVE DUPLICATED RECIPES
print(f"STEP 5: REMOVING DUPLICATED RECIPES.")
duplicated_recipes = ["legatza_kokotea","esne_frijitua","txokolate_trufa_bonboia"]
no_duplicated_recipes = recipes_group[~recipes_group["recipe_new"].isin(duplicated_recipes)]

#save new data
recipe_base_grouped_path= os.path.join(data_tmp_folder, "recipe_titles_grouped.csv")
no_duplicated_recipes.to_csv(recipe_base_grouped_path, index = False)

# STEP6: FIND MISS DISH ORDER RECIPES 
print(f"STEP 6: FIND MISS DISH ORDER RECIPES .")
no_order, without_order = gdf.count_empty_dish_order(no_duplicated_recipes)
print(f"\tExist {without_order} recipes without dish_order information. Try to complete by ingredients logic.")

# AND TRY TO COMPLETE THEM by ingredients logic, i.e.: haragia, arraina second dishes.. 
dish_order_completed = gdf.complete_dish_order(no_duplicated_recipes, conf)
no_order, without_order = gdf.count_empty_dish_order(dish_order_completed)
print(f"\tAfter correct exist {without_order} recipes without dish_order information. Try to complete asking user.")

# ASK USER TO COMPLETE THOSE RECIPES WITHOUT DISH ORDER
dish_order_completed2 = gdf.complete_dish_order_by_user(dish_order_completed, no_order, conf)   

#save to check
dish_order_completed_path= os.path.join(data_tmp_folder, "recipe_with_dish_order_completed.csv")
dish_order_completed2.to_csv(dish_order_completed_path, index = False)

# STEP7: FIND MISS COOK TECHNIQUE ITEMS
print(f"STEP 7: FIND MISS COOK TECHNIQUE RECIPES .")
no_tech, without_tech = gdf.count_empty_techniques(dish_order_completed2)
print(f"\tExist {without_tech} recipes without cook techniques information. Try to complete by term logic.")

#  AND TRY TO FIX THEM by technique synonims logic, i.e.: uretan <-> egosi.. 
recipes_with_techs = gdf.complete_tech_by_synonims(dish_order_completed2, conf)
no_tech, without_tech = gdf.count_empty_techniques(recipes_with_techs)
print(f"\tAfter correct exist {without_tech} recipes without cook techniques information.")

#save to check
technique_completed_path= os.path.join(data_tmp_folder, "recipe_with_techs_completed.csv")
recipes_with_techs.to_csv(technique_completed_path, index = False)


# STEP8: TRY TO CLASIFY NO TECH RECIPES BY ORIGIN i.e.: tagliatelle, caprese <-> italia.. 
print(f"STEP 8: TRY TO CLASIFY NO TECH RECIPES BY ITS ORIGIN .")
recipe_df_new = gdf.complete_origin(recipes_with_techs, conf)
no_tech_orig, without_tech_orig = gdf.count_empty_tech_and_origin(recipe_df_new)
print(f"\tThere are {without_tech_orig} recipes without cook technique and origin.")  

#save to check
origin_completed_path= os.path.join(data_tmp_folder, "recipe_with_origin_completed.csv")
recipe_df_new.to_csv(origin_completed_path, index = False)

# STEP9: REPLACE RECIPES TEXT TO DETECT EASIER: MORE INGREDIENTS
print(f"STEP 9: JOIN COMPOSED TERMS IN RECIPES TO DETECT EASIER: MORE INGREDIENTS.")
recipe_df_corrected = gdf.replace_recipe_words(recipe_df_new, "recipe_new", conf["DICT_TO_JOIN"])

# STEP10: GET MORE INGREDIENTS PER RECIPES
print(f"STEP 10: GET INGREDIENTS BY RECIPES.")
unwanted_words = gdf.obtain_nowanted_terms(conf) + conf["UNWANTED_OTHER_TERMS"]
recipes_with_ingredients = gdf.get_recipe_ingredients(recipe_df_corrected, "recipe_new", "ingredients", unwanted_words)

# STEP11: CORRECT INGREDIENTS MISSPELLINGS 
print(f"STEP 11: CORRECT RECIPE TITLES AND INGREDIENTS MISSPELLINGS.")
# correct recipe titles and column name
recipes_with_ingredients["recipe_new"] = recipes_with_ingredients["recipe_new"].apply(lambda x: gdf.correct_capitalization(x, "recover"))
recipes_with_ingredients.rename(columns={'recipe_new': 'recipe'}, inplace=True)

# remove ingredients suffixes 
recipe_ingredients_corrected = gdf.remove_suffixes(recipes_with_ingredients, "ingredients", conf["SUFFIXES"])

#save to check
recipes_extra_ingredients_path= os.path.join(data_tmp_folder, "recipes_with_ingredients.csv")
recipe_ingredients_corrected.to_csv(recipes_extra_ingredients_path, index = False)
print(f"\tCheck {recipes_extra_ingredients_path} file and correct minor ingredients terms.")
print(f"\tSave final file here: {conf['DATA_PATH']} as {conf['RECIPES_FILE_NAME']}")
print(f"END")