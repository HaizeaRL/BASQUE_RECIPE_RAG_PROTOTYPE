import os
import sys
from urllib.parse import urljoin
import yaml
from pathlib import Path
import pandas as pd

# Add the parent directory (where modules is located) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import recipe_web_scrapping_functions as rwsf

# Read config file
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conf = yaml.safe_load(Path(os.path.join(root_path, "config.yaml")).read_text())

# Create data folder
data_folder = os.path.join(root_path, conf["DATA_PATH"])
os.makedirs(data_folder, exist_ok=True)

# Define save path
similar_recipes_file = os.path.join(data_folder, conf["SIMILAR_RECIPES_FILE_NAME"])
similar_recipes_file_checked = os.path.join(data_folder, conf["SIMILAR_NEW_FILE_NAME"])

# If the file does not exist, execute the steps until its creation
if not os.path.exists(similar_recipes_file):
    # WEB SCRAP TO GET BASE RECIPE LIST
    base_url = conf["BASE_URL"]
    url = urljoin(base_url, conf["URL_COMPLEMENT"])
    print(f"STEP 1: APPLYING WEB SCRAPPING TO OBTAIN RECIPE BASE LIST: {url} ...")
    ingredients_list, recipe_dict = rwsf.scrap_all_recipies(url, base_url)
    recipes_df = rwsf.recipe_dict_into_df(recipe_dict)
    print(f"\tRECIPES TABLE OBTAINED.")

    # PREPROCESS BASE RECIPE LIST: Group recipes by ingredients, get titles similarities to remove duplicates.
    print(f"STEP 2: PREPROCESSING BASE RECIPE LIST...")
    recipe_df_grouped = rwsf.group_titles_with_ingredients(recipes_df)
    print(f"\tRECIPES GROUPED BY INGREDIENTS.")

    # Get similar recipes list to correct by user
    print(f"\tGETTING SIMILAR RECIPES LIST TO BE CORRECTED BY THE USER.")
    recipe_pairs = rwsf.get_recipe_pairs_to_compare(recipe_df_grouped)  # Get recipe pairs
    # Compare and save recipes
    rwsf.compare_recipes_by_scapy(conf, recipe_pairs, similar_recipes_file)
else:
    # TODO CORRECT
    # If the file exists, proceed from asking the user to mark duplicates
    print(f"PLEASE CHECK AND MARK DUPLICATE RECIPES TO REMOVE:")
    rwsf.get_user_input_and_update(conf, pd.read_csv(similar_recipes_file), similar_recipes_file_checked)

if os.path.exists(similar_recipes_file_checked):
    # REMOVE DUPLICATES ACCORDING TO USER ANSWERS
    print(f"STEP 3: REMOVE DUPLICATES ACCORDING TO USER ANSWERS...")

    # COMPLETE RECIPE TABLE WITH DISH_ORDER AND COOK_TECHNIQUE DATA

    # GET DICTIONARIES
    '''print(f"STEP 4: APPLYING WEB SCRAPPING TO OBTAIN RECIPE COOK TECHNIQUES & DISH_ORDER RELATION FROM: {url} ...")
    techniques = [conf["CATEGORY_PREFIX"]+ item for item in conf["TECHNIQUES_CATEGORIES"]]
    techniques_dict = rwsf.scrap_recipes_by_category_list(url, base_url,techniques)
    print(f"\tRECIPES BY COOK TECHNIQUES OBTAINED. GROUPED IN TOTAL OF {len(techniques_dict.keys())} COOK TECHNIQUES.")

    dish_order_categories = [conf["CATEGORY_PREFIX"]+ item for item in conf["DISH_ORDER_CATEGORIES"]]
    order_dict = rwsf.scrap_recipes_by_category_list(url, base_url,dish_order_categories)
    print(f"\tRECIPES BY DISH ORDER OBTAINED. GROUPED IN: {order_dict.keys()}.")'''

    # COMPLETE DATA 

