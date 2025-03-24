import os
import sys
import yaml
from pathlib import Path
import pandas as pd

# Add the parent directory (where modules is located) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import database_functions as dbf


# Read config file
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conf = yaml.safe_load(Path(os.path.join(root_path, "config.yaml")).read_text(encoding="utf-8"))

# Reference to data folder
data_folder = os.path.join(root_path, conf["DATA_PATH"])
os.makedirs(data_folder, exist_ok=True)

# Create database and tables
db_path = os.path.join(data_folder, conf["DATABASE_NAME"])
dbf.create_db(db_path)

# Check database creation
dbf.check_database_tables(db_path)

# Obtain data and insert to tables
# ingredient_categories
recipe_df = pd.read_csv(os.path.join(data_folder, conf["RECIPES_FILE_NAME"]), sep=";")
ingredient_categories = dbf.get_ingredient_categories(recipe_df)
dbf.save_list_in_db(db_path, "ingredient_category", ingredient_categories)

# dish_order
dish_order_l = sorted(recipe_df["order"].unique().tolist())
dbf.save_list_in_db(db_path, "dish_order", dish_order_l)

# cook_technique
techniques_l = sorted([item for item in recipe_df["technique"].unique().tolist() if pd.notna(item)])
dbf.save_list_in_db(db_path, "cook_technique", techniques_l)

# localization
localization_l = sorted([item for item in recipe_df["origin"].unique().tolist() if pd.notna(item)])
dbf.save_list_in_db(db_path, "localization", localization_l)

# ingredient 
excel_file_path = os.path.join(data_folder,conf["INGREDIENT_CATEGORIES_FILENAME"])
dbf.save_ingredient_categories(db_path, excel_file_path, ingredient_categories)

# recipes
dbf.save_recipe(db_path, recipe_df)

# recipe_ingredient_category
dbf.save_recipe_ingredient_category(db_path, recipe_df)

# recipe_ingredient
dbf.save_recipe_ingredient(db_path, recipe_df)


# check data
dbf.show_table_data(db_path, "ingredient_category")
dbf.show_table_data(db_path, "dish_order")
dbf.show_table_data(db_path, "cook_technique")
dbf.show_table_data(db_path, "localization")
dbf.show_table_data(db_path, "ingredient", True) # limit result to 10
dbf.show_table_data(db_path, "recipe", True) # limit result to 10 
dbf.show_table_data(db_path, "recipe_ingredient_category", True) # limit result to 10 
dbf.show_table_data(db_path, "recipe_ingredient", True) # limit result to 10