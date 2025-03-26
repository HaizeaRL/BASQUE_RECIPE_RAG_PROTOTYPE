from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
import re

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
                print(f"- {table}: {table_descriptions[table]}")

    return db, tables_to_visualize

# Function to extract only SQL from response markdown.
def extract_sql_from_response(response):
    pattern = r"```sql\n(SELECT .*?);\n```"  # Captura solo la consulta SQL
    match = re.search(pattern, response, re.DOTALL)
    return match.group(1) if match else None

def get_rows_number_all_tables(database_path, llm, conf, dest_lang):
     
    # get database tables
    db, tables = get_database_tables(database_path, conf, True, False, dest_lang) # without bridge tables, no print tables

    # Iterate in tables and obtain corresponding result
    print("---\n<MODEL>:", lif.translate_text_with_Elia("Here you have 'table name': - [(number of rows)]' relation:\n", "en", dest_lang))
    for table in tables:
        chain = create_sql_query_chain(llm, db)
        response = chain.invoke({"question": f"How many {table}s are in {table} table? give sql"})
        sql_query = extract_sql_from_response(response)
        result =db.run(sql_query)
        # visualize row number per table
        print(f"'{table}':- {result}")
       

def get_recipe_count_per_category(database_path, llm, recipe_table, category_tables, dest_lang):

    # Get database
    db = get_database(database_path)
    
    # database conection ctrl
    if not db:
        # print text in corresponding dest_lang language
        text_to_translate = f"Could not connect to database. Revise past database url: {database_path}"
        print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))
        return None  # Explicitly return None when database connection fails


    # create sql chain
    chain = create_sql_query_chain(llm, db)

    # iterate category_table. 
    print("---\n<MODEL>:", lif.translate_text_with_Elia("Here is the amount of recipes in each category:\n", "en", dest_lang))
    for category_table in category_tables:
        # Create the SQL query instruction
        response = chain.invoke({
            "question": (
                        f"Give a complete SQL query to get how many {recipe_table}s are in {recipe_table} per each {category_table} element."
                        f"The query should use a LEFT JOIN to the {category_table} and return the corresponding {category_table} value instead of just the ID. "
                        f"The query should handle cases where the {category_table}_id is NULL, ensuring those rows are still included in the result. "
                        f"The query should be in the form 'SELECT COALESCE({category_table}.{category_table}, 'Unknown') as name, COUNT(*) FROM {recipe_table} "
                        f"LEFT JOIN {category_table} ON {recipe_table}.{category_table}_id = {category_table}.{category_table}_id GROUP BY name;'"
                        )
        })
        # Extract the SQL query from the response
        sql_query = extract_sql_from_response(response)
        #print(sql_query)
        
        # Run the SQL query on the database
        result = db.run(sql_query)

        print(f"{category_table}' taulan:")
        print(result)
        '''for row in result:
            if len(row) >= 2:
                name, value = row[:2]  # Tomar solo los primeros dos elementos
                name = "Sailkatu gabeak" if name == "Unknown" else name
                print(f"- {name}: ({value})")'''   

def get_ingredient_category_top3(database_path, llm, principal_table, worst = False, dest_lang= "eu"):

    # Get database
    db = get_database(database_path)
    
    # database conection ctrl
    if not db:
        # print text in corresponding dest_lang language
        text_to_translate = f"Could not connect to database. Revise past database url: {database_path}"
        print(lif.translate_text_with_Elia(text_to_translate, "en", dest_lang))
        return None  # Explicitly return None when database connection fails
    
    # create sql chain
    chain = create_sql_query_chain(llm, db)

   
    # obtain joining tables from principal_table Example: recipe_ingredient_category relates: recipe and ingredient_category tables
    pos = principal_table.find('_')
    join_table1 = principal_table[0:pos]
    join_table2 = principal_table[pos+1:len(principal_table)]

    # top3 best or worst logic
    order_type= "DESC"
    if worst:
        order_type = "ASC"
   
    response = chain.invoke({
        "question" :  (
            f"Give a complete SQL query that gives top3 best (more recipes) or worst (less recipes) ingredient categories."
            f"The query should be in the form 'SELECT COUNT({join_table1}.recipe_id), {join_table2}.ingredient_category "
            f"FROM {principal_table} "
            f"JOIN {join_table1} ON {principal_table}.recipe_id = {join_table1}.recipe_id "
            f"JOIN {join_table2} ON {principal_table}.category_id = {join_table2}.category_id "
            f"GROUP BY {join_table2}.ingredient_category "
            f"ORDER BY COUNT({join_table1}.recipe_id) {order_type} LIMIT 3;'"
        )
    })   

    # Extract the SQL query from the response
    sql_query = extract_sql_from_response(response)
    #print(sql_query)
    
    # Run the SQL query on the database
    result = db.run(sql_query)
    print(result)

    '''
    if worst:
        print("---\n<MODEL>:", lif.translate_text_with_Elia("Here are top 3 ingredient categories with less recipes:\n", "en", dest_lang))
        for res in result:
            print(f"- {name}: ({value})")    
    else:
        print("---\n<MODEL>:", lif.translate_text_with_Elia("Here are top 3 ingredient categories with most recipes::\n", "en", dest_lang))
        for res in result:
            print(f"- {name}: ({value})") 
    '''       

    