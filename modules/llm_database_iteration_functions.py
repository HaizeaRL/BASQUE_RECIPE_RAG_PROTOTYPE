from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chains import create_sql_query_chain
from langchain.llms import Ollama
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

    # get database 
    db = SQLDatabase.from_uri(f"sqlite:///{database_path}")

    # return if exist
    return db if db else None



def get_database_tables(database_path, conf, user_mode=False, visualize_data = True, dest_lang = "eu"):

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
    parts = sql_string.split("\n\nSQLQuery: ")
    question = parts[0].replace("Question: ", "").strip()
    queries = parts[1].strip().split("\n")

    return {
        "question": question,
        "queries": queries
    }


def extract_sql_from_response(response):
    pattern = r"```sql\n(SELECT .*?);\n```"  # Captura solo la consulta SQL
    match = re.search(pattern, response, re.DOTALL)
    return match.group(1) if match else None

def get_rows_number_all_tables(database_path, llm, conf, dest_lang):
     
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
       