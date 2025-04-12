from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chains import create_sql_query_chain
import re
import ast

from modules import llm_iteration_functions as lif

table_descriptions = {
    "cook_technique": "Sukaldatze teknikak: erregosi, labekatu...",
    "dish_order": "Platera ordena: lehen platera, bigarren platera...",
    "ingredient": "Errezetetan erabiltzen diren banakako osagaien zerrenda.",
    "ingredient_category": "Osagaien kategoriak, hala nola barazkiak, haragia, etab.",
    "localization": "Errezeten kokapenari buruzko informazioa.",
    "recipe": "Errezetak eta haien xehetasunak, osagaiak eta prestaketa-urratsak biltzen dituen taula."
}

def get_database(database_path):

    """
    Function that connects to an SQLite database using the provided database path and returns the database object 
    if the connection is successful. If the connection fails or the database does not exist, it returns None.

    Parameters:
        database_path (str): The path to the SQLite database file.

    Returns:
        db (SQLDatabase or None): The database object if the connection is successful, otherwise None.
    """

    # get database 
    db = SQLDatabase.from_uri(f"sqlite:///{database_path}")

    # return if exist
    return db if db else None



def get_database_tables(database_path, conf, user_mode=False, visualize_data = True, dest_lang = "eu"):

    """
    Function that connects to an SQLite database, retrieves the list of usable tables, and optionally filters out 
    bridge tables and visualizes the data. If the connection to the database fails or no tables are found, the function 
    returns None. The function also supports language translation for error messages and table descriptions.

    Parameters:
        database_path (str): The path to the SQLite database file.
        conf (dict): A configuration dictionary containing settings, including a list of bridge tables under the key "BRIDGE_TABLES".
        user_mode (bool, optional): A flag that, when set to True, filters out bridge tables from the list of tables to visualize. Defaults to False.
        visualize_data (bool, optional): A flag that controls whether the function should print the list of tables and their descriptions. Defaults to True.
        dest_lang (str, optional): The target language for translation of messages. Defaults to "eu" (Basque).

    Returns:
        tuple: A tuple containing:
            - db (SQLDatabase or None): The connected database object if the connection is successful, otherwise None.
            - tables_to_visualize (list): A list of table names to be visualized (filtered based on user_mode), or an empty list if no tables exist.
    """

    # Get database
    db = get_database(database_path)
    
    # database conection ctrl
    if not db:
        # print text in corresponding dest_lang language
        text_to_translate = f"Could not connect to database. Revise past database url: {database_path}"
        print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))
        return None  # Explicitly return None when database connection fails

    # Get database table list
    tables = db.get_usable_table_names()
    
    # database table existing  ctrl
    if not tables:
        # print text in corresponding dest_lang language
        print(lif.translate_text_with_Elia(f"No table found in the database.", "en", dest_lang))
        return None  # No tables found, return None

    tables_to_visualize = tables  
    if user_mode:
        # filter tables no present: bridge tables
        tables_to_visualize = [table for table in tables if table not in conf["BRIDGE_TABLES"]]

    # Visualize data if correspond in corresponding dest_lang language
    if visualize_data:
        print("---\n<MODEL>:", lif.translate_text_with_Elia("The following tables are found in the database:\n", "en", dest_lang))
        for table in tables_to_visualize:
                print(f"\t- '{table}': {table_descriptions[table]}")

    return db, tables_to_visualize

def parse_sql_string(sql_string):

    """
    Function that parses a formatted SQL string, extracting the question and SQL queries from it. The function assumes that 
    the input string contains a question preceded by "Question: " and SQL queries preceded by "SQLQuery: ", separated by two newlines. 

    Parameters:
        sql_string (str): The SQL string containing a question and one or more SQL queries.

    Returns:
        dict: A dictionary with two keys:
            - "question" (str): The extracted question from the string.
            - "queries" (list): A list of SQL queries extracted from the string.
    """

    parts = sql_string.split("\n\nSQLQuery: ")
    question = parts[0].replace("Question: ", "").strip()
    queries = parts[1].strip().split("\n")

    return {
        "question": question,
        "queries": queries
    }


def extract_sql_from_response(response):
    """
    Function that extracts an SQL query from a given response string. The function looks for an SQL query enclosed within 
    triple backticks (```) with the `sql` syntax, specifically capturing a query starting with `SELECT` and ending with a semicolon.

    Parameters:
        response (str): The response string containing the SQL query enclosed in triple backticks.

    Returns:
        str or None: The extracted SQL query if found, or None if no matching query is found.
    """

    pattern = r"```sql\n(SELECT .*?);\n```"  # Captura solo la consulta SQL
    match = re.search(pattern, response, re.DOTALL)
    return match.group(1) if match else None


def get_rows_number_all_tables(database_path, llm, conf, dest_lang):

    """
    Function that retrieves the number of rows for each table in the database. The function first connects to the database, excludes 
    bridge tables, and generates SQL queries to count the rows in each table. It then executes the queries and prints the 
    results for each table, excluding bridge tables, with the number of rows.

    Parameters:
        database_path (str): The file path of the database to connect to.
        llm (object): The language model tool used to generate SQL queries.
        conf (dict): A dictionary containing configurations, including details about bridge tables.
        dest_lang (str): The destination language code for translation of output text (e.g., "eu" for Basque).

    Returns:
        None: This function prints the results of the query execution directly and does not return any value.
    """     
    # get database tables
    db, tables = get_database_tables(database_path, conf, True, False, dest_lang) # without bridge tables, no print tables

     # database conection ctrl
    if not db:
        # print text in corresponding dest_lang language
        text_to_translate = f"Could not connect to database. Revise past database url: {database_path}"
        print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))
        return None  # Explicitly return None when database connection fails
    
    # get queries by question   
    write_query = create_sql_query_chain(llm, db)
    chain = write_query
    queries = chain.invoke({"question": "How many rows are in each table?"})

    # parse result, separating question from queries
    parsed_result = parse_sql_string(queries)

    # execute each query and visualize the result
    print("---\n<MODEL>:", lif.translate_text_with_Elia("Here you have table name and its number of rows relation:", "en", dest_lang))
    execute_query = QuerySQLDataBaseTool(db=db)
    for query in parsed_result["queries"]:
        # get query result
        result = execute_query.invoke({'query': query})

        if result:

            # transform query from str to list
            data_list = ast.literal_eval(result)

            # deduce table name from query
            table_name = query.split("FROM")[1].strip().rstrip(";")

            if table_name in tables: # No print bridge table data
                # print text tranlated to basque
                print(f"\t-'{table_name}' taulak: {data_list[0][0]} errenkada ditu.")

def get_recipe_count_per_category(database_path, llm, category_tables, dest_lang):

    """
    Function that retrieves the count of recipes per category from the database. For each category table, the function generates 
    and executes an SQL query to count the number of recipes associated with each category name (not ID) using a 
    LEFT JOIN between the recipe table and the category table. The results are printed, showing the category name 
    and the corresponding number of recipes.

    Parameters:
        database_path (str): The file path of the database to connect to.
        llm (object): The language model tool used to generate SQL queries.
        category_tables (list): A list of category tables for which to count the recipes.
        dest_lang (str): The destination language code for translation of output text (e.g., "eu" for Basque).

    Returns:
        None: This function prints the results directly and does not return any value.
    """
    # Get database
    db = get_database(database_path)
    
    # database conection ctrl
    if not db:
        # print text in corresponding dest_lang language
        text_to_translate = f"Could not connect to database. Revise past database url: {database_path}"
        print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))
        return None  # Explicitly return None when database connection fails

    # iterate category_table. 
    print("---\n<MODEL>:", lif.translate_text_with_Elia("Here is the amount of recipes in each category:", "en", dest_lang))
    
    write_query = create_sql_query_chain(llm, db)
    chain = write_query
    for table in category_tables:
        # create each tables corresponding question text
        question_text = f"Generate an SQL query to count the number of recipes per {table} name (not ID) using a SINGLE LEFT JOIN between the recipe and {table} tables. Do not include any additional joins. Give sql only."

        # ask to generate sql
        answer = chain.invoke({"question": question_text})

        if answer:
            # extract sql from model answer and obtain the result 
            execute_query = QuerySQLDataBaseTool(db=db)
            query_result = execute_query.invoke({'query': extract_sql_from_response(answer)})

            if query_result:
                # iterate tupla list and visualize data correcly per category_table
                print(f"\n'{table}' taulan:")

                # convert resulted str to list to handle better
                data_list = ast.literal_eval(query_result)
                for item in data_list:
                    # separate tuple values
                    name, value = item
                    # correct unknows values
                    name = "saikatu gabeak" if name == None else name
                    # print values
                    print(f"\t-'{name}': {value} errezeta.")

def get_ingredient_category_top3(database_path,  worst = False, dest_lang= "eu"):

    """
    Function that retrieves and prints the top 3 ingredient categories with the most or fewest recipes in the database. 
    The function counts the number of recipes associated with each ingredient category, orders them 
    based on the count (either in descending or ascending order), and then displays the top 3 categories 
    along with their recipe counts.

    Parameters:
        database_path (str): The file path of the database to connect to.
        worst (bool, optional): If True, returns the categories with the fewest recipes. 
                                 Defaults to False, which returns the categories with the most recipes.
        dest_lang (str, optional): The destination language code for translation of output text 
                                    (e.g., "eu" for Basque). Defaults to "eu".

    Returns:
        None: This function prints the top 3 ingredient categories and their respective recipe counts 
              directly and does not return any value.
    """
    # Get database
    db = get_database(database_path)
    
    # database conection ctrl
    if not db:
        # print text in corresponding dest_lang language
        text_to_translate = f"Could not connect to database. Revise past database url: {database_path}"
        print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))
        return None  # Explicitly return None when database connection fails

    # determine order by and texts    
    if worst:
        order_term = "ASC"
        text = "the fewest"
        text_eu= "gutxien"
    else:
        order_term = "DESC"
        text = "the most"
        text_eu= "gehien"

    # direct query
    sql_query = f"""SELECT ingredient_category.ingredient_category, COUNT(*) as count
                    FROM recipe_ingredient_category
                    JOIN recipe ON recipe_ingredient_category.recipe_id = recipe.recipe_id
                    JOIN ingredient_category ON recipe_ingredient_category.category_id = ingredient_category.category_id
                    GROUP BY ingredient_category.ingredient_category
                    ORDER BY COUNT(*) {order_term}
                    LIMIT 3;"""
    
    # obtain result from database
    result =db.run(sql_query)

    # visualize result in correct way
    if result:
        # convert string to corresponding list form
        data_list = ast.literal_eval(result)

        # iterate resulted list
        print("---\n<MODEL>:", lif.translate_text_with_Elia(f"Here the top 3 ingredient categories with {text} amount recipes:", "en", dest_lang))
        for item in data_list:
            # get each items element
            cat, cnt = item
            # create text and visualize result
            print(f"\t-'{cat}' osagai kategoria da errezetatan '{text_eu}' ageri denetako bat. Zehazki: {cnt} errezetatan ageri da.")
       


def get_most_used_ingredient_per_category(database_path, dest_lang):
    """
    Function that retrieves and prints the most used ingredient for each ingredient category in the database.
    The function counts the occurrences of each ingredient within its category and identifies 
    the most frequently used ingredient for each category. It then displays the category name, 
    the most used ingredient, and the count of recipes where the ingredient appears.

    Parameters:
        database_path (str): The file path of the database to connect to.
        dest_lang (str): The destination language code for translation of output text 
                         (e.g., "eu" for Basque).

    Returns:
        None: This function prints the most used ingredient per ingredient category and its 
              recipe count directly and does not return any value.
    """
    # Get database
    db = get_database(database_path)
    
    # database conection ctrl
    if not db:
        # print text in corresponding dest_lang language
        text_to_translate = f"Could not connect to database. Revise past database url: {database_path}"
        print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))
        return None  # Explicitly return None when database connection fails

    # direct query
    sql_query = """SELECT ingredient_category,  ingredient, count
        FROM (
        SELECT 
            ic.category_id,
            ic.ingredient_category,
            i.ingredient,
            COUNT(ri.ingredient_id) AS count,
            ROW_NUMBER() OVER (PARTITION BY ic.category_id ORDER BY COUNT(ri.ingredient_id) DESC) AS row_num
        FROM recipe r
        JOIN recipe_ingredient ri ON r.recipe_id = ri.recipe_id
        JOIN ingredient i ON ri.ingredient_id = i.ingredient_id
        JOIN ingredient_category ic ON i.category_id = ic.category_id
        GROUP BY ic.category_id, ic.ingredient_category, i.ingredient
        ) AS subquery
        WHERE row_num = 1;"""
    

    # obtain result from database
    result =db.run(sql_query)

    # visualize result in correct way
    if result:
        # convert string to corresponding list form
        data_list = ast.literal_eval(result)

        # iterate resulted list
        print("---\n<MODEL>:", lif.translate_text_with_Elia("Here is presented the most used ingredient per ingredient category:", "en", dest_lang))
        for item in data_list:
            # get each items element
            cat, ing, cnt = item

            # create text and visualize result
            print(f"\t-'{cat}' osagai kategorian 'gehien' ageri den osagaia: '{ing}' da. Zehazki: {cnt} errezetatan agertzen da.")
    
    
def get_and_filter_recipe_by_term(db, llm,json_dict, term, dest_lang= "eu"):

    """
    Function that retrieves and filters recipes from the database based on a given search term. 
    The function first attempts to find recipes that contain the term in the recipe's name. 
    If no results are found, it tries to find recipes using a list of ingredients provided 
    in the input JSON dictionary. The results are returned in the form of a list of recipe names 
    with their corresponding URLs.

    Parameters:
        db (SQLDatabase): The database object used to run queries.
        llm (OpenAI): The language model used to generate SQL queries.
        json_dict (dict): A dictionary containing the ingredients list, which is used to 
                          suggest recipes when no recipes match the search term.
        term (str): The search term used to filter recipes by their name.
        dest_lang (str): The destination language code for translation of output text 
                         (e.g., "eu" for Basque). Default is "eu".

    Returns:
        None: This function prints out a list of recipe names with their corresponding URLs 
              that match the search criteria. If no matching recipes are found, it will attempt 
              to provide suggestions based on ingredients.
    """   
    # ask to generate sql
    write_query = create_sql_query_chain(llm, db)
    chain = write_query
    question_text = f"Create an SQL query that retrieves the 'recipe' and 'url' columns from the recipe table, filtering recipes that contain the given {term} in the 'recipe' column. Ensure that no JOIN operations are used and apply the filter directly on the recipe table. Provide only the SQL query."
    answer = chain.invoke({"question": question_text})

    if answer:
        # extract sql from answer
        query = extract_sql_from_response(answer)
        
        # execute query
        execute_query = QuerySQLDataBaseTool(db=db)
        result = execute_query.invoke({'query': query})

        if result:
            # convert string to corresponding list form
            data_list = ast.literal_eval(result)
        
            # visualize result
            print("---\n<MODEL>:", lif.translate_text_with_Elia("Here are the proposals:", "en", dest_lang))
            for i, item in enumerate(data_list, start=1):  # start numeration from 1
    
                # get each items element
                recipe, url = item  
                text_to_translate = f"-{i}. proposal: {recipe}\nThe preparation instructions are here: {url}."
                print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))
        elif json_dict["ingredients"] is not None and len(json_dict["ingredients"]) != 0:

            # print model message saying that we will try to find solution according to ingredients
            list_ingredients_translated = [lif.translate_text_with_Elia(item, "en", dest_lang) for item in json_dict["ingredients"]]
            
            text_to_translate = f"""I don't have a specific recipe associated with '{term}' but that recipe uses {list_ingredients_translated} ingredients so I will try to suggest (at most) 5 recipes that can be made with these ingredients."""
            print("---\n<MODEL>:", lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))

            # ask to generate sql
            write_query = create_sql_query_chain(llm, db)
            chain = write_query
            question_text = f"""
                    Create an SQL query that retrieves the 'recipe' and 'url' columns from the exact 'recipe' table,  
                    Match using LEFT JOINS the 'recipe', 'recipe_ingredient', and 'ingredient' tables and    
                    use given ingredient name list {list_ingredients_translated} to filter ingredients.
                    Limit the results to 5 recipes.  
                    Do not include any other JOINs or additional tables. Provide only the SQL query between ```s.
                    """
            answer = chain.invoke({"question": question_text})
            if answer:
                # extract sql from answer
                query = extract_sql_from_response(answer)
                
                # execute query
                execute_query = QuerySQLDataBaseTool(db=db)
                result = execute_query.invoke({'query': query})

                if result:
                    # convert string to corresponding list form
                    data_list = ast.literal_eval(result)
                
                    # visualize result
                    for i, item in enumerate(data_list, start=1):  # start numeration from 1
            
                        # get each items element
                        recipe, url = item  
                        text_to_translate = f"-{i}. proposal: {recipe}\nThe preparation instructions are here: {url}."
                        print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))




def process_json_dict_and_get_bbdd_result(json_dict, database_path , llm, dest_lang= "eu"):

    """
    Function that retrieves recipes or food-related information from the database 
    based on the data provided in the input JSON dictionary. It checks whether the 
    user is asking for a specific recipe or food and then calls the appropriate 
    function to filter recipes based on the given terms.

    Parameters:
        json_dict (dict): A dictionary containing the query parameters, including 
                          flags for specific requests (like `concrete_recipe_ask` 
                          or `concrete_food_ask`) and the names of the recipe 
                          or food (`recipe_name` or `food_name`).
        database_path (str): The path to the SQLite database used for querying.
        llm (OpenAI): The language model used to generate SQL queries.
        dest_lang (str): The destination language code for translation of output text 
                         (e.g., "eu" for Basque). Default is "eu".

    Returns:
        None: This function does not return a value. Instead, it prints out results
              directly by querying the database and filtering recipes or food names 
              based on the provided terms.
    """

    # Get database
    db = get_database(database_path)
    
    # database conection ctrl
    if not db:
        # print text in corresponding dest_lang language
        text_to_translate = f"Could not connect to database. Revise past database url: {database_path}"
        print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))
        return None  # Explicitly return None when database connection fails

    
    if json_dict["concrete_recipe_ask"] and json_dict["recipe_name"] is not None:        
        get_and_filter_recipe_by_term(db, llm, json_dict, json_dict["recipe_name"], dest_lang)
        
    elif json_dict["concrete_food_ask"] and  json_dict["food_name"] is not None:
        get_and_filter_recipe_by_term(db,llm, json_dict, json_dict["food_name"], dest_lang)