import os
import sys
from urllib.parse import urljoin

# Add the parent directory (where modules is located) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import data_base_creation_functions as dbcf


# Create database and tables
db_path = dbcf.create_db()

# Check database creation
dbcf.check_database_tables(db_path)
dbcf.show_ingredients_table(db_path) # Show ingredients
dbcf.show_recipes_table(db_path) # Show recipes

# obtain first ingredients and recipes web scrapping
base_url = "https://eu.wikibooks.org/wiki/"
url = urljoin(base_url, "Sukaldaritza_liburua/Azala")
ingredient_list, recipes = dbcf.scrap_all_recipes(url, base_url)

# check tables data:
dbcf.show_ingredients_table(db_path) # Show ingredients
dbcf.show_recipes_table(db_path) # Show recipes

