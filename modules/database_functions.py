import sqlite3
from openpyxl import load_workbook
import pandas as pd

def create_db(db_path):
    """
    Function that creates a database with the necessary tables for managing recipes, ingredients, categories, 
    dish orders, cooking techniques, and localization.

    Parameters:
        db_path (str): The file path where the SQLite database will be created.

    Returns:
        None: The function creates the database and tables but does not return any value.
    """
  
    # Create the database
    conn = sqlite3.connect(db_path)

    # get cursor
    cursor = conn.cursor()

    # Create category table
    cursor.execute('''
       CREATE TABLE ingredient_category (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_category TEXT NOT NULL UNIQUE
        );
        ''')
    
    

    # Create ingredients table: ingredient related to ingredient_category
    cursor.execute('''
       CREATE TABLE ingredient (
            ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient TEXT NOT NULL UNIQUE,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES ingredient_category(category_id) ON DELETE SET NULL
        );
        ''')

    # Create dish_order table
    cursor.execute('''
        CREATE TABLE dish_order (
            dish_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_order TEXT NOT NULL UNIQUE
        );
    ''')

    # Create cook techniques table
    cursor.execute('''
        CREATE TABLE cook_technique (
            cook_technique_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cook_technique TEXT NOT NULL UNIQUE
        );
    ''')

    # Create recipe localization table
    cursor.execute('''
        CREATE TABLE localization (
            localization_id INTEGER PRIMARY KEY AUTOINCREMENT,
            localization TEXT NOT NULL UNIQUE
        );
    ''')

    # Create recipe - dish-order, cook-technique , localization table, & url
    cursor.execute('''
        CREATE TABLE recipe (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe TEXT NOT NULL UNIQUE,
            dish_order_id INTEGER,
            cook_technique_id INTEGER,
            localization_id INTEGER,
            url TEXT NOT NULL,
            FOREIGN KEY (dish_order_id) REFERENCES dish_order(dish_order_id) ON DELETE SET NULL,
            FOREIGN KEY (cook_technique_id) REFERENCES cook_technique(cook_technique_id) ON DELETE SET NULL,
            FOREIGN KEY (localization_id) REFERENCES localization(localization_id) ON DELETE SET NULL
        );
    ''')

    # recipe_ingredient_category relation table
    cursor.execute('''
        CREATE TABLE recipe_ingredient_category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique ID for each entry
            recipe_id INTEGER  NOT NULL,
            category_id INTEGER  NOT NULL, 
            FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES ingredient_category(category_id) ON DELETE CASCADE
        );
    ''')

    # recipe_ingredient relation table
    cursor.execute('''
        CREATE TABLE recipe_ingredient (
            recipe_ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique ID for each entry
            recipe_id INTEGER NOT NULL,
            ingredient_id INTEGER,  -- Nullable field
            FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES ingredient(ingredient_id) ON DELETE CASCADE
        );
    ''')

    # commit and close
    conn.commit()
    conn.close()

def check_database_tables(db_path):
    """
    Function that checks and prints the names of all tables in the specified SQLite database.

    Parameters:
        db_path (str): The file path to the SQLite database.

    Returns:
        None: The function connects to the database, queries the list of tables, and prints the names of 
              the tables, excluding the internal `sqlite_sequence` table. It does not return any value.
    """

    # Connect to the database
    conn = sqlite3.connect(db_path)

    # get cursor
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

def get_ingredient_categories(df):
    """
    Function that extracts and returns a sorted list of unique ingredient categories from the given DataFrame.

    Parameters:
        df (DataFrame): A pandas DataFrame containing a column "ingredient_group", which holds comma-separated ingredient categories.

    Returns:
        list: A sorted list of unique ingredient categories, with any duplicates removed and categories stripped of leading/trailing spaces.
    """

    ingredient_categories=[]
    for index, row in df.iterrows():
        groups = row["ingredient_group"].split(",")
        for group in groups:
            if group.strip() not in ingredient_categories:
                ingredient_categories.append(group.strip())
    return sorted(ingredient_categories)

def save_list_in_db(db_path, table_column, value_list):
    """
    Function that saves a list of values into a specified database table column, 
    ensuring that duplicate values are ignored.

    Parameters:
        db_path (str): The path to the SQLite database file.
        table_column (str): The name of the table and column to insert values into (in the format 'table_name.column_name').
        value_list (list): A list of values to be inserted into the specified table column.

    Returns:
        None: The function does not return anything, it commits changes directly to the database.
    """

    # open database connection
    conn = sqlite3.connect(db_path)

    # get cursor
    cursor = conn.cursor()

    # Dynamically construct the SQL query with table and column names
    query = f"INSERT OR IGNORE INTO {table_column} ({table_column}) VALUES (?)"

    # Insert values
    cursor.executemany(query, [(value,) for value in value_list])

    # commit and close
    conn.commit()
    conn.close()


def save_ingredient_categories(db_path, excel_file_path, category_list):

    """
    Function that saves ingredient categories and their respective ingredients from an Excel file into a database.
    It first checks if the category exists in the database, then reads the ingredients from the corresponding Excel 
    sheet and inserts them into the database under the correct category.

    Parameters:
        db_path (str): The path to the SQLite database file.
        excel_file_path (str): The path to the Excel file containing the ingredient categories and ingredients.
        category_list (list): A list of category names that need to be processed.

    Returns:
        None: The function does not return anything, it commits changes directly to the database.
    """

    # open database connection
    conn = sqlite3.connect(db_path)

    # get cursor
    cursor = conn.cursor()

    # open excel file to check sheetnames
    wb = load_workbook(excel_file_path, read_only=True) 

    # get each categories ingredients to insert into table
    for category in category_list:
        if category in wb.sheetnames:
            
            # get category_id
            select_query = "SELECT category_id FROM ingredient_category WHERE ingredient_category = ?"
            cursor.execute(select_query, (category,))
            res = cursor.fetchone()
            category_id = res[0] if res else None

            if not category_id:
                continue  # jump if category not exist

            # read ingredients from corresponding sheet
            df1 = pd.read_excel(excel_file_path, sheet_name=category)
            ingredient_list = sorted(df1["ingredients"].dropna().unique().tolist())

            if ingredient_list:
                # Insert data in bbdd
                insert_query = "INSERT OR IGNORE INTO ingredient (ingredient, category_id) VALUES (?, ?)"
                cursor.executemany(insert_query, [(value, category_id) for value in ingredient_list])

    # commit and close
    conn.commit()
    conn.close()

def save_recipe(db_path, df):
    """
    Function that saves recipe data from a DataFrame into the `recipe` table of a database. 
    For each recipe in the DataFrame, it retrieves the associated dish order, cooking technique, and origin 
    from their respective tables and inserts the complete recipe record into the `recipe` table.

    Parameters:
        db_path (str): The path to the SQLite database file.
        df (DataFrame): A pandas DataFrame containing recipe data, including recipe name, order, technique, origin, and URL.

    Returns:
        None: The function does not return anything; it commits changes directly to the database.
    """
    # Connect to the database
    conn = sqlite3.connect(db_path)

    # get cursor
    cursor = conn.cursor()

    # iterate recipe df to complete ddbb recipe table
    for index, row in df.iterrows():
        # get recipe title and url
        recipe = row["recipe"]   
        url = row["url"]

        # get dish_order_id
        dish_order_id = None
        if row["order"] is not None:
            select_query = "SELECT dish_order_id FROM dish_order WHERE dish_order = ?"
            cursor.execute(select_query, (row["order"],))
            res = cursor.fetchone()
            dish_order_id = res[0] if res else None
            
        # get cook_technique_id
        cook_technique_id = None
        if row["technique"] is not None:
            select_query = "SELECT cook_technique_id FROM cook_technique WHERE cook_technique = ?"
            cursor.execute(select_query, (row["technique"],))
            res = cursor.fetchone()
            cook_technique_id = res[0] if res else None
            
        # get localization_id
        localization_id = None
        if row["origin"] is not None:
            select_query = "SELECT localization_id FROM localization WHERE localization = ?"
            cursor.execute(select_query, (row["origin"],))
            res = cursor.fetchone()
            localization_id = res[0] if res else None

        # create insert query
        insert_query = "INSERT OR IGNORE INTO recipe (recipe, dish_order_id, cook_technique_id, localization_id, url) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(insert_query, (recipe, dish_order_id, cook_technique_id, localization_id, url))

    # commit and close
    conn.commit()
    conn.close()

def save_recipe_ingredient_category(db_path, df):
    """
    Function that saves the relationship between recipes and their ingredient categories 
    into the `recipe_ingredient_category` table in the database. The function iterates over the 
    DataFrame containing recipe data, splits ingredient categories, and inserts the corresponding 
    recipe and ingredient category IDs into the database.

    Parameters:
        db_path (str): The path to the SQLite database file.
        df (DataFrame): A pandas DataFrame containing recipe data with columns such as `recipe` 
                        and `ingredient_group`, where `ingredient_group` contains comma-separated 
                        ingredient categories.

    Returns:
        None: The function does not return anything; it commits changes directly to the database.
    """

    # Connect to the database
    conn = sqlite3.connect(db_path)

    # get cursor
    cursor = conn.cursor()

    # iterate recipe df to complete ddbb recipe_ingredient_category table
    for index, row in df.iterrows():
        # get recipe and recipe group values
        recipe = row["recipe"]
        ingredient_group = row["ingredient_group"]
        
        # get corresponding information
        if ingredient_group is not None and recipe is not None:
            # split categories
            groups = ingredient_group.split(", ")
            print(groups)

            # for each group get info and insert values
            for group in groups:

                # get recipe_id
                select_query = "SELECT recipe_id FROM recipe WHERE recipe = ?"
                cursor.execute(select_query, (recipe,))
                res = cursor.fetchone()
                recipe_id = res[0] if res else None

                # get category_id
                select_query = "SELECT category_id FROM ingredient_category WHERE ingredient_category = ?"
                cursor.execute(select_query, (group,))
                res = cursor.fetchone()
                ingredient_category_id = res[0] if res else None

                # if data is obtained insert into database table
                if not recipe_id :
                    print(f"ERROR recipe: {recipe} does not exist.")
                    continue  # jump if category not exist
                else:
                    # create insert query
                    insert_query = "INSERT OR IGNORE INTO recipe_ingredient_category (recipe_id, category_id ) VALUES (?, ?)"
                    cursor.execute(insert_query, (recipe_id, ingredient_category_id))

    # commit and close
    conn.commit()
    conn.close()

def save_recipe_ingredient(db_path, df):

    """
    Function that saves the relationship between recipes and their ingredients into the `recipe_ingredient` 
    table in the database. The function iterates over the DataFrame containing recipe data, extracts ingredients 
    for each recipe, and inserts the corresponding recipe and ingredient IDs into the database.

    Parameters:
        db_path (str): The path to the SQLite database file.
        df (DataFrame): A pandas DataFrame containing recipe data with columns such as `recipe` and `ingredients`, 
                        where `ingredients` contains a comma-separated list of ingredients.

    Returns:
        None: The function does not return anything; it commits changes directly to the database.
    """
    # Connect to the database
    conn = sqlite3.connect(db_path)

    # get cursor
    cursor = conn.cursor()

    # iterate recipe df to complete ddbb recipe_ingredient table
    for index, row in df.iterrows():
        recipe = row["recipe"]

        if not pd.isna(row["ingredients"]):   
            ingredients = row["ingredients"].split(", ")
            for ingredient in ingredients:

                # get recipe_id
                select_query = "SELECT recipe_id FROM recipe WHERE recipe = ?"
                cursor.execute(select_query, (recipe,))
                res = cursor.fetchone()
                recipe_id = res[0] if res else None

                # get ingredient_id if exist
                ingredient_id = None
                if ingredient is not None:
                    select_query = "SELECT ingredient_id FROM ingredient WHERE ingredient = ?"
                    cursor.execute(select_query, (ingredient,))
                    res = cursor.fetchone()
                    ingredient_id = res[0] if res else None

                # create dynamic query and insert data
                if recipe_id:
                    # create insert query
                    insert_query = "INSERT OR IGNORE INTO recipe_ingredient (recipe_id, ingredient_id) VALUES (?, ?)"
                    cursor.execute(insert_query, (recipe_id, ingredient_id))

    # commit and close
    conn.commit()
    conn.close()

def show_table_data(db_path, table, limit=None):
    """
    Function that retrieves and displays data from a specified table in the database. The function constructs 
    a dynamic SQL query to fetch the data from the given table, with an optional limit on the number of rows 
    returned, and then prints out the results.

    Parameters:
        db_path (str): The path to the SQLite database file.
        table (str): The name of the table to retrieve data from.
        limit (int, optional): The maximum number of rows to display. If not specified, all rows will be retrieved.

    Returns:
        None: The function does not return anything; it prints the results directly.
    """

    # Connect to the database
    conn = sqlite3.connect(db_path)

    # get cursor
    cursor = conn.cursor()

    # Dynamically construct the SQL query with table and column names
    if limit:
        query = f"SELECT * FROM {table} LIMIT 10;"
    else:
        query = f"SELECT * FROM {table};"
    
    # Query to check data in the specified table (if any)
    cursor.execute(query)  # Retrieve all rows
    ingredients = cursor.fetchall()
    
    if len(ingredients) >0:
        print(f"\nSample data from '{table}' table:")
        for row in ingredients:
            print(row)
    else:
        print(f"'{table}' table is empty.")

    # Close the connection
    conn.close()