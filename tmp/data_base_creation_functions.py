import sqlite3
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import string

# Function to create SQLite database and tables
import sqlite3
import os

def create_db():
    # Get the absolute path of the 'data' folder (which is at the root level of your project)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_folder = os.path.join(project_root, 'data')

    # Ensure the 'data' folder exists
    os.makedirs(data_folder, exist_ok=True)

    # Set the database path
    db_path = os.path.join(data_folder, 'recipes.db')

    # Create the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create ingredients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient TEXT UNIQUE
        );
    ''')

    # Create recipes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER,
            recipe_title TEXT,
            recipe_url TEXT,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
        );
    ''')

    # Create techniques table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS techniques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER UNIQUE,  
            technique TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        );
    ''')

    # Create order table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_order (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER UNIQUE,  
            recipe_order TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        );
    ''')

    conn.commit()
    conn.close()
    return db_path

# Function to save ingredients to the database
def save_ingredients(ingredients_list):
    # Get the absolute path of the 'data' folder (which is at the root level of your project)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_folder = os.path.join(project_root, 'data')
    
    db_path = os.path.join(data_folder, 'recipes.db')
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    for ingredient in ingredients_list:
        cursor.execute('''
            INSERT OR IGNORE INTO ingredients (ingredient)
            VALUES (?)
        ''', (ingredient,))
    
    conn.commit()
    conn.close()


def save_ingredient(ingredient):
    # Get the absolute path of the 'data' folder (which is at the root level of your project)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_folder = os.path.join(project_root, 'data')
    
    db_path = os.path.join(data_folder, 'recipes.db')
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    cursor.execute(''' 
        INSERT OR IGNORE INTO ingredients (ingredient) 
        VALUES (?) 
    ''', (ingredient,))


    conn.commit()
    conn.close()


# Function to save recipes to the database
def save_recipes(ingredient, recipes_list):
    # Get the absolute path of the 'data' folder (which is at the root level of your project)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_folder = os.path.join(project_root, 'data')
    
    db_path = os.path.join(data_folder, 'recipes.db')
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    # Get the ingredient_id from the ingredients table
    cursor.execute('''
        SELECT id FROM ingredients WHERE ingredient = ?
    ''', (ingredient,))
    ingredient_id = cursor.fetchone()

    if ingredient_id:
        ingredient_id = ingredient_id[0]
    else:
        conn.close()
        return  # Ingredient should exist, but just in case

    for recipe in recipes_list:
        for title, url in recipe.items():
            cursor.execute('''
                INSERT INTO recipes (ingredient_id, recipe_title, recipe_url)
                VALUES (?, ?, ?)
            ''', (ingredient_id, title, url))
    
    conn.commit()
    conn.close()


def scrap_all_recipes(url, base_url):
    """
    Function that applies web scraping to find all Basque recipes from URL and retrieve recipes per
    ingredients saving in sqllite tables.
    
    Parameters:
        url (str): The URL of the web page to scrape.
        base_url (str): The base URL of the web page to continue scrapping through sub links.

    Returns:
        list: A list of all ingredients found on the web page.
    """

    # Fetch the main page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Dictionary to store results
    ingredients_list = set()
    recipes = {}

    # Find all <a> elements with title starting with "Kategoria:Osagaia:"
    for link in soup.find_all("a", attrs={"title": re.compile(r"^Kategoria:Osagaia:")}):
        # Get the href attribute to open the linked page
        sub_url = link.get("href")
        
        # Get also the ingredient of the recipe and add to ingredients_list
        ingredient = link.text.split(":")[1]
        ingredients_list.add(ingredient)
        
        if sub_url:
            sub_response = requests.get(urljoin(base_url, sub_url))
            sub_soup = BeautifulSoup(sub_response.text, "html.parser")
        
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
                                recipe_url =  urljoin(base_url, link2.get("href"))
                                
                                # Add to dictionary
                                recipe_dict = {recipe_title: recipe_url}
                                
                                # Append to the list of recipes
                                recipes_list.append(recipe_dict)
            
            # Group recipes by ingredient in a dictionary
            recipes[ingredient] = recipes_list

    # Save ingredients and recipes to the database
    save_ingredients(ingredients_list)
    for ingredient, recipes_list in recipes.items():
        save_recipes(ingredient, recipes_list)

    return ingredients_list, recipes

def check_database_tables(db_path):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to check if the tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # Print out the list of tables
    print("Tables in the database:")
    for table in tables:
        if table[0] != "sqlite_sequence":
            print("\t- ",table[0])  # Print the name of each table
    
    # Close the connection
    conn.close()

def show_ingredients_table(db_path):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to check data in the 'ingredients' table (if any)
    cursor.execute("SELECT * FROM ingredients;")  # Retrieve the first 5 rows
    ingredients = cursor.fetchall()
    
    if len(ingredients) >0:
        print("\nSample data from 'ingredients' table:")
        for row in ingredients:
            print(row)
    else:
        print("'ingredients' table is empty.")

    # Close the connection
    conn.close()

def show_recipes_table(db_path):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to check data in the 'recipes' table (if any)
    cursor.execute("SELECT * FROM recipes LIMIT 5;")  # Retrieve the first 5 rows
    recipes = cursor.fetchall()

    if len(recipes) >0:
        print("\nSample data from 'recipes' table:")
        for row in recipes:
            print(row)
    else:
        print("'recipes' table is empty.")

    # Close the connection
    conn.close()

# TODO WEB SCRAP TECHNIQUES
# TODO WEB SCRAP ORDERS