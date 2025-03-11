import os
import sys
from urllib.parse import urljoin
import yaml
from pathlib import Path
import pandas as pd
import json

# Add the parent directory (where modules is located) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import recipe_web_scrapping_functions as rwsf

# Read config file
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conf = yaml.safe_load(Path(os.path.join(root_path, "config.yaml")).read_text())

# Create data folder
data_folder = os.path.join(root_path, conf["DATA_PATH"])
os.makedirs(data_folder, exist_ok=True)

# Define save paths
ingredients_file = os.path.join(data_folder, conf["INGREDIENTS_FILE_NAME"])
temporal_recipes_file= os.path.join(data_folder, conf["RECIPES_FILE_NAME_TMP"])
similar_recipes_file = os.path.join(data_folder, conf["SIMILAR_RECIPES_FILE_NAME"])
similar_recipes_file_checked = os.path.join(data_folder, conf["SIMILAR_NEW_FILE_NAME"])
subgroup_terms_file = os.path.join(data_folder, conf["SUBGROUP_TERMS_FILE_NAME"])
subgroup_terms_new_file = os.path.join(data_folder, conf["SUBGROUP_NEW_FILE_NAME"])
recipes_by_sym_and_user= os.path.join(data_folder, conf["RECIPES_COMPLETED"])
last_recipe_file = os.path.join(data_folder, conf["RECIPES_LAST_FILE_NAME"])

# Define web scrapping urls
base_url = conf["BASE_URL"]
url = urljoin(base_url, conf["URL_COMPLEMENT"])

# If the file does not exist, execute the steps until its creation
if not os.path.exists(similar_recipes_file):
    # WEB SCRAP TO GET BASE RECIPE LIST   
    print(f"STEP 1: APPLYING WEB SCRAPPING TO OBTAIN RECIPE BASE LIST: {url} ...")
    ingredients_list, recipe_dict = rwsf.scrap_all_recipies(url, base_url)
    # save ingredients as dataframe
    ingredients_df = pd.DataFrame(ingredients_list, columns=['ingredients'])
    ingredients_df.to_csv(ingredients_file,index = False)

    # convert recipe dict into df
    recipes_df = rwsf.recipe_dict_into_df(recipe_dict)
    print(f"\tINGREDIENTS AND RECIPE BASE TABLE OBTAINED.")

    # PREPROCESS BASE RECIPE LIST: Group recipes by ingredients, get titles similarities to remove duplicates.
    print(f"STEP 2: PREPROCESSING BASE RECIPE LIST...")
    recipe_df_grouped = rwsf.group_titles_with_ingredients(recipes_df)
    print(f"\tRECIPES GROUPED BY INGREDIENTS.")

    print(f"\tGETTING SIMILAR RECIPES LIST TO BE CORRECTED BY THE USER.")    
    # clean a little recipe titles & save recipe baseline df
    recipe_df_grouped["cleaned"] = rwsf.process_column(conf, recipe_df_grouped["recipe"])
    recipe_df_grouped.to_csv(temporal_recipes_file, index = False)

    # get recipe pairs & compare to find similar recipes
    recipe_pairs = rwsf.get_recipe_pairs_to_compare(recipe_df_grouped)  # Get recipe pairs    
    model_path = os.path.join(conf["DATA_PATH"], conf["STANZA_LANG"])
    rwsf.compare_recipes(conf, model_path, recipe_pairs, similar_recipes_file) # Compare and save recipes

    # If the file exists, proceed from asking the user to mark duplicates
    print(f"PLEASE CHECK AND MARK DUPLICATE RECIPES TO REMOVE:")
    rwsf.get_user_input_and_update(conf, pd.read_csv(similar_recipes_file), similar_recipes_file_checked)

if os.path.exists(similar_recipes_file_checked):    
    print(f"STEP 3: REMOVE DUPLICATES ACCORDING TO USER ANSWERS...")

    # get list of elements to find and remove
    user_checked_file = pd.read_csv(similar_recipes_file_checked)
    recipe_base_df= pd.read_csv(temporal_recipes_file)

    # discover rows to remove according to user, discover coindicencies and remove wrong items
    wrong_recipe_titles = user_checked_file[user_checked_file["equal"] == 1]["incorrect"].tolist()
    recipe_base_df = recipe_base_df[~recipe_base_df["cleaned"].isin(wrong_recipe_titles)]
    print(f"\t{len(wrong_recipe_titles)} RECIPES REMOVE FROM TABLE.")
    
    # save modified recipe table again
    recipe_base_df.to_csv(temporal_recipes_file, index = False)

if not os.path.exists(os.path.join(data_folder,"order_dict.txt")) and \
    not os.path.exists(os.path.join(data_folder,"techniques_dict.txt")):  

    print(f"STEP 4: APPLYING WEB SCRAPPING TO OBTAIN RECIPE COOK TECHNIQUES & DISH_ORDER RELATION FROM: {url} ...")
    
    # get techniques
    techniques = [conf["CATEGORY_PREFIX"]+ item for item in conf["TECHNIQUES_CATEGORIES"]]
    techniques_dict = rwsf.scrap_recipes_by_category_list(url, base_url, techniques)
    print(f"\tRECIPES BY COOK TECHNIQUES OBTAINED. GROUPED IN TOTAL OF {len(techniques_dict.keys())} COOK TECHNIQUES.")

    # get dish order recipes relation
    dish_order_categories = [conf["CATEGORY_PREFIX"]+ item for item in conf["DISH_ORDER_CATEGORIES"]]
    order_dict = rwsf.scrap_recipes_by_category_list(url, base_url, dish_order_categories)
    print(f"\tRECIPES BY DISH ORDER OBTAINED. GROUPED IN: {order_dict.keys()}.")

    # save tech, dish_order dicts and last recipe table to validate results
    with open(os.path.join(data_folder,"order_dict.txt"), "w") as f:
        json.dump(order_dict, f, indent=4)

    with open(os.path.join(data_folder,"techniques_dict.txt"), "w") as f:
        json.dump(techniques_dict, f, indent=4)

if os.path.exists(os.path.join(data_folder,"order_dict.txt")) and \
    os.path.exists(os.path.join(data_folder,"techniques_dict.txt")):  

    # Recover dictionaries
    with open(os.path.join(data_folder, "order_dict.txt"), "r") as f:
        order_dict = json.load(f)

    with open(os.path.join(data_folder, "techniques_dict.txt"), "r") as f:
        techniques_dict = json.load(f)

    # and base df    
    recipe_base_df= pd.read_csv(temporal_recipes_file)

    print(f"STEP 5: JOINING RECIPE TABLE WITH COOK TECHNIQUE AND DISH ORDER")
    recipe_base_df["order"] = None
    recipe_base_df["technique"] = None
    for index, row in recipe_base_df.iterrows(): 
        recipe_base_df.at[index, "order"] = rwsf.find_category_by_recipe(order_dict, row["recipe"])
        recipe_base_df.at[index, "technique"] = rwsf.find_category_by_recipe(techniques_dict, row["recipe"])

    recipe_base_df.to_csv(temporal_recipes_file, index = False)
   
    print("STEP 6: COMPLETE MISSING VALUES")
    print("CHECKING DISH ORDER AND COMPLETING...")
    recipe_df_new = rwsf.complete_dish_order_by_synomims_and_user(recipe_base_df, conf)

    '''path = os.path.join(data_folder, "recipe_tmp1.csv")
    recipe_df_new.to_csv(path, index = False)'''

    print("CHECKING COOK TECHNIQUES AND COMPLETING BY SYNONYMS...")
    no_tech, without_tech = rwsf.count_empty_techniques(recipe_df_new)
    if without_tech !=0:
        print(f"\tThere are {without_tech} recipes without cook technique. Let's try to complete with synonims...")
        recipe_df_new = rwsf.complete_tech_by_synonims(recipe_df_new, conf)
        no_tech1, without_tech1 = rwsf.count_empty_techniques(recipe_df_new)
        if without_tech1 !=0: 
            print(f"\tAfter corrected with synonims are {without_tech1} recipes without cook technique.")
            
    '''path = os.path.join(data_folder, "recipe_tmp2.csv")
    recipe_df_new.to_csv(path, index = False)'''

    print("CHECKING IF RECIPES CAN BE CLASSIFIED BY ORIGINS...")
    recipe_df_new = rwsf.complete_origin(recipe_df_new, conf)
    no_tech_orig, without_tech_orig = rwsf.count_empty_tech_and_origin(recipe_df_new)
    if without_tech_orig !=0:
        print(f"\tThere are {without_tech_orig} recipes without cook technique and origin.")   

    # save changed df
    recipe_df_new.to_csv(recipes_by_sym_and_user, index = False)

if os.path.exists(recipes_by_sym_and_user):  
    print("STEP 7: GET INGREDIENT SUBGROUPS AND CORRECT MISSPELLINGS..")
