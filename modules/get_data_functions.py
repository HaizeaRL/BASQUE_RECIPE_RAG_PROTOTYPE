import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import pandas as pd

def scrap_recipes_titles_and_url(sub_soup, base_url):
    """
    Function that scrapes a web page to retrieve all Basque recipe titles and their corresponding URLs.

    Parameters:
        sub_soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of the webpage or section to scrape.
        base_url (str): The base URL of the website to resolve relative URLs to absolute URLs.

    Returns:
        list: A list of dictionaries where each dictionary contains a recipe title as the key and the corresponding URL as the value.
    """
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
                        recipe_url = urljoin(base_url, link2.get("href"))
                        
                        # Add to dictionary
                        recipe_dict = {recipe_title: recipe_url}
                        
                        # Append to the list of recipes
                        recipes_list.append(recipe_dict)
    return recipes_list

def scrap_all_recipies(url, base_url):
    """
    Function that applies web scraping to find all basque recipies from url and retrieve recipes per
    ingredients.
    
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
    recipes =  {}

    # Find all <a> elements with title starting with "Kategoria:Osagaia:"
    for link in soup.find_all("a", attrs={"title": re.compile(r"^Kategoria:Osagaia:")}):
        # Get the href attribute to open the linked page   
        sub_url = link.get("href")  
        
        # get also de ingredient of the recipe and add to ingredients_list
        ingredient = link.text.split(":")[1]
        ingredients_list.add(link.text.split(":")[1])
        
        if sub_url:
            sub_response = requests.get(urljoin(base_url, sub_url))    
            sub_soup = BeautifulSoup(sub_response.text, "html.parser")    
        
            # obtain recipies title and urls by ingredients
            recipies_list = scrap_recipes_titles_and_url(sub_soup,base_url)
            
            # Group recipes by ingredient in a dictionary
            recipes[ingredient] = recipies_list

    # return actual ingredient list and recipes per ingredients
    return ingredients_list, recipes

def scrap_recipes_titles(sub_soup):
    """
    Function that scrapes recipe titles from a given HTML soup object by searching for specific elements
    and matching titles. It returns a list of recipes that are present in the provided recipes list.

    Parameters:
        sub_soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML of the page to scrape.
      
    Returns:
        list: A list of recipe titles found in the provided HTML that are also present in the input recipes list.
    """
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
                        
                        # add recipe to list
                        recipes_list.append(recipe_title)
    return recipes_list

def scrap_recipes_by_category_list(url, base_url , category_list): 
    """
    Function that scrapes recipe titles categorized by specific categories from a web page.
    It fetches the main page, extracts category-specific links, then scrapes recipe titles 
    under each category and returns them in a dictionary.

    Parameters:
        url (str): The URL of the main page to scrape.
        base_url (str): The base URL to resolve relative links.
        category_list (list): A list of categories to match and extract from the page.

    Returns:
        dict: A dictionary where the keys are category names and the values are lists of matching recipe titles.
    """
    # Fetch the main page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Dictionary to store results
    response_dictionary = {}

    # Find all <a> elements with title starting with category_list elements
    for link in soup.find_all("a", href=True):
        if link.get('title') in category_list:
            key = link.text
            sub_url = link.get("href") 
            if sub_url:
                sub_response = requests.get(urljoin(base_url, sub_url))    
                sub_soup = BeautifulSoup(sub_response.text, "html.parser")    
            
                # obtain recipe titles list
                recipes_list = scrap_recipes_titles(sub_soup)
                # save in the dictionary
                response_dictionary[key] = recipes_list      

    return response_dictionary

def find_category_by_recipe (dictionary , recipe_title):
    """
    Finds the category (key) associated with a given recipe title in a dictionary.

    Parameters:
        dictionary (dict): A dictionary where keys are categories and values are lists of recipe titles.
        recipe_title (str): The title of the recipe to search for.

    Returns:
        str: The category (key) associated with the given recipe title, or None if not found.
    """
    for key in dictionary.keys():
        for recipe in dictionary.get(key):       
            if recipe == recipe_title:
                return key

def recipes_dict_to_df(recipes_dict, techniques_dict, order_dict):
    recipes_tab=[]

    # Iterate over the categories and their corresponding recipes
    for ingredient, recipe_list in recipes_dict.items():
        for recipe in recipe_list:
            for recipe_title, url in recipe.items():
                
                technique_aux = find_category_by_recipe (techniques_dict , recipe_title)
                dish_order_aux = find_category_by_recipe (order_dict , recipe_title)
                
                technique = technique_aux
                dis_order = dish_order_aux

                # Convert to lower if correspond (i.e., if the value is not None)
                if technique_aux is not None:
                    technique = technique_aux.lower()

                if dish_order_aux is not None:
                    dis_order = dish_order_aux.lower()
                
                # todo add url
                recipes_tab.append({"ingredient_group": ingredient.lower(), "recipe":recipe_title,
                                    "order":dis_order, "technique": technique, 
                                    "url": url})
    
    # convert table to df
    return pd.DataFrame(recipes_tab)

def correct_capitalization(text, action):
    """
    Corrects the capitalization of the input text based on the specified action.

    Parameters:
        text (str): The input string that needs its capitalization corrected.
        action (str): The action to perform on the text. Can be either:
                      - "remove": Converts all words to lowercase.
                      - "recover": Capitalizes the first word and converts the rest to lowercase.

    Returns:
        str: The corrected text after applying the capitalization rule.
    """
    
    if action == "remove":
        # Split the text into words
        words = text.split()
        
        # Make the first word capitalized and the rest in lowercase
        text = [word.lower() for word in words]        
    
    elif action == "recover":
        # Split the text into words
        words = text.split()  # Assuming you want to split by spaces
        
        # Capitalize the first word and make the rest lowercase
        words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
        # Join the words back into a single string
        text = " ".join(words).replace("_"," ")
    
    return text

def correct_recipe_titles(text):
    """
    Processes a given text string by:
    
    1. Removing unwanted characters (quotes, `.jpg`, extra spaces).
    2. Correcting capitalization using `correct_capitalization(text)`.
    3. Merging trailing numbers with the preceding word (e.g., "esnekia 2" → "esnekia2").
    4. Returning the formatted string with words joined by underscores.

    input:
        text (str): The input text to process.

    Returns:
        str: The formatted text with corrections applied.
    """
    # remove unwanted characters
    text = text.replace('"', '').replace('“', '').replace("'",'').replace(",",'').replace('.jpg','').strip()

    # correct capitalization
    words = correct_capitalization(text, "remove")
    
    # Correct numerization
    if len(words) > 1 and words[-1].isdigit():  
        words[-2] = words[-2] + words[-1]  # Append the number to the previous word
        words.pop()  # Remove the last word
    
    # Join the words back into a single string
    return '_'.join(words)

def replace_words(df, col1, word_dict):
    """
    Replaces occurrences of specific words in the 'recipe_new' column of a DataFrame based on a provided dictionary.

    This function scans the 'recipe_new' column of the DataFrame and replaces words that match the keys in `word_dict` 
    with their corresponding values. The replacements ensure that only full words are matched and modified, preventing 
    partial substitutions within other words.

    Input:
        df (DataFrame): The DataFrame where word replacements should be applied.
        col1 (str): Column to filter and change
        word_dict (dict): A dictionary where keys represent words to find, and values are their replacements.

    Returns:
        DataFrame: The modified DataFrame with a new column 'recipe_new2' containing the updated text.

    Example:
        word_dict = {"antxua": "antxoa", "bakailo": "bakailao"}
        df = pd.DataFrame({"recipe_new": ["antxua_bakailo_saltsan"]})
        replace_words(df, word_dict)  
        # Output: DataFrame with 'recipe_new2' as 'antxoa_bakailao_saltsan'
    """

    # Iterate over the rows of the DataFrame
    for index, row in df.iterrows():

        # Split the title into words using "_"
        words = row[col1] .split("_")

        # Replace words using word_dict if a key exists as a substring
        updated_words = []
        
        for word in words:
            # Check for any word in word_dict that appears as a substring
            updated_word = word
            for key in word_dict:
                if key in word:  # Check if the key is part of the word
                    updated_word = updated_word.replace(key, word_dict[key])  # Replace substring
            updated_words.append(updated_word)

        # Join the updated words back into a single string
        updated_title = "_".join(updated_words)
                
        # Add the updated title as a new column in the DataFrame
        df.at[index, col1] = updated_title
    
    return df

def group_titles_with_ingredients(df):
    """
    Function that groups a DataFrame by recipe titles and aggregates the associated ingredients, order, 
    technique, origin, and recipe URLs. The function ensures that the values are unique and sorted within 
    each group.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data with columns such as 'recipe', 'ingredient_group', 
        'order', 'technique'and 'recipe_url'.

    Returns:
        DataFrame: A pandas DataFrame where each row represents a unique recipe with aggregated ingredients,
        and URLs.
    """
    # Group by 'recipe' and aggregate:
    grouped_df = (df.groupby('recipe_new', as_index=False)
              .agg({
                  "ingredient_group": lambda x: ', '.join(set(x.dropna())),
                  "order": lambda x: ', '.join(set(x.dropna())),
                  "technique": lambda x: ', '.join(set(x.dropna())),
                  "url": lambda x: x.dropna().iloc[0]  # first not null value, only one link
              }))
    return grouped_df

def count_empty_dish_order(df):
    """
    Counts the recipes that have no dish order specified in the DataFrame.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data, with an 'order' column.

    Returns:
        tuple: A tuple where the first element is a list of recipe titles with no dish order,
               and the second element is the count of recipes with no dish order.
    """
    no_dish_order = []   
    for index, row in df.iterrows():
        if not row["order"]:  # Check for NaN (missing) values
            no_dish_order.append(row["recipe_new"])
    return no_dish_order, len(no_dish_order)

def complete_dish_order(df, conf):
    """
    Completes the 'order' column in the DataFrame based on the recipe's ingredient and title.
    The function assigns a dish order category to recipes that do not have one, using predefined rules 
    and the provided configuration.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data with columns such as 'recipe', 
                         'ingredient', and 'order'.
        conf (dict): A dictionary containing configuration, including:
            - "INGREDIENTS_FIRST_DISH_ORDER", "INGREDIENTS_SECOND_DISH_ORDER", and "INGREDIENTS_THIRD_DISH_ORDER" 
              (lists of ingredients to categorize the dish order).
            - "DISH_ORDER_CATEGORIES" (list of categories for dish orders).
            - "FIRST_ORDER_TERMS" (list of terms that help identify first-order dishes).

    Returns:
        DataFrame: The updated DataFrame with completed 'order' columns for all recipes.
    """
    for index, row in df.iterrows():
        ingredient = [ingredient.strip() for ingredient in row['ingredient_group'].split(',')]
        dish_order = row['order']
        
        # Check if no order and if any ingredient matches the first dish order
        if not row["order"] and any(ing.lower() in [item.lower() for item in conf["INGREDIENTS_FIRST_DISH_ORDER"]] for ing in ingredient):                
            df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][0].lower()  # lehen platerak    
        
        # Check if no order and if any ingredient matches the second dish order
        elif not row["order"] and any(ing.lower() in [item.lower() for item in conf["INGREDIENTS_SECOND_DISH_ORDER"]] for ing in ingredient):
            df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][1].lower()  # bigarren platerak 
        
        # Check if no order and if any ingredient matches the third dish order
        elif not row["order"] and any(ing.lower() in [item.lower() for item in conf["INGREDIENTS_THIRD_DISH_ORDER"]] for ing in ingredient):
            # Correct: guakamole
            if any(term.lower() in row['recipe_new'].lower() for term in ["guakamole"]):
                df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][0].lower()  # lehen platerak
            
            # Correct: eperrak txokolate saltsan
            elif any(term.lower() in row['recipe_new'].lower() for term in ["eperrak"]):
                df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][1].lower()  # bigarren platerak
            else:             
                df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][2].lower()  # azkenburukoak
        
        # If there's already a dish order and ingredient is "barazkia"
        elif row["order"] and any(ing.lower() == "barazkia" for ing in ingredient):
            # Correct: barazki eta txekor azpizun erregosia
            if any(term.lower() in row['recipe_new'].lower() for term in ["erregosi"]):
                df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][1].lower()  # bigarren platerak
        
        # Check if any of the first dish order terms are in the recipe title
        if any(term.lower() in row['recipe_new'].lower() for term in conf["FIRST_DISH_ORDER_TERMS"]):
            # Correct wrongly classified
            df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][0].lower()  # lehen platerak

    return df


def ask_for_dish_menu_order(recipe, conf):
    """
    Prompts the user to select the dish order category for a given recipe from a list of options.
    The function displays a menu with categories and allows the user to choose one, or quit.

    Parameters:
        recipe (str): The name of the recipe for which the dish order is being determined.
        conf (dict): A dictionary containing the configuration, specifically the list of dish order categories 
                     under the key "DISH_ORDER_CATEGORIES".

    Returns:
        list: A list containing the selected dish order category.
    """
    #["1. Lehen platerak", "2. Bigarren platerak", "3. Azkenburukoak"]
    options = [str(idx + 1) +". "+ item for idx, item in enumerate(conf["DISH_ORDER_CATEGORIES"])]
    end_char = "q"

    while True:
        print(f"\nDetermine '{recipe}' dish order. This dish is: ")
        for option in options:
            print(option)
        print(f"Enter '{end_char}' to quit.")

        choice = input("Select an option (1-3) or 'q' to quit: ").strip()

        if choice == end_char:
            break
        elif choice in ["1", "2", "3"]:
            if int(choice) == 1:
                return conf["DISH_ORDER_CATEGORIES"][0].lower() # lehen platerak
            elif int(choice) == 2:
                return conf["DISH_ORDER_CATEGORIES"][1].lower() # bigarren platerak
            else:
                return conf["DISH_ORDER_CATEGORIES"][2].lower() # azkenburukoak
        else:
            print("Invalid choice! Please enter 1, 2, or 3.")

def complete_dish_order_by_user(recipe_df, no_order_list, conf):
    """
    Completes the 'order' column in the DataFrame by prompting the user to select the dish order category 
    for recipes that do not have an order, based on the recipe titles in the 'no_order_list'.

    Parameters:
        recipe_df (DataFrame): A pandas DataFrame containing recipe data with columns such as 'recipe' and 'order'.
        no_order_list (list): A list of recipe titles that do not have a dish order assigned.
        conf (dict): A dictionary containing configuration, specifically the list of dish order categories 
                     under the key "DISH_ORDER_CATEGORIES".

    Returns:
        DataFrame: The updated DataFrame with completed 'order' columns for the recipes that were missing an order.
    """
    for index, row in recipe_df.iterrows():
        if row['recipe_new'] in no_order_list:
            row["order"] = ask_for_dish_menu_order(row['recipe_new'], conf)
    return recipe_df

def count_empty_techniques(df):
    """
    Counts the recipes that have no technique specified in the DataFrame.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data with a 'technique' column.

    Returns:
        tuple: A tuple where the first element is a list of recipe titles with no technique,
               and the second element is the count of recipes with no technique.
    """   
    no_tech = []   
    for index, row in df.iterrows():
        if not row["technique"]:  
            no_tech.append(row["recipe_new"])
    return no_tech, len(no_tech)

def complete_tech_by_synonims(df, conf):
    """
    Completes the 'technique' column in the DataFrame by assigning appropriate techniques based on recipe names 
    and predefined subcategories of techniques. The function checks the recipe name for terms that match specific 
    technique subcategories and assigns the corresponding technique.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data, with columns such as 'recipe' and 'technique'.
        conf (dict): A dictionary containing technique subcategories for different techniques, with keys like 
                     "CARPACCIO_TECH_SUBCATEGORIES", "EGOSI_TECH_SUBCATEGORIES", etc., and values being lists 
                     of terms to match in the recipe names.

    Returns:
        DataFrame: The updated DataFrame with completed 'technique' columns for all recipes.
    """

    # complete techniques column as much as possible
    for index, row in df.iterrows():
        tech = row['technique']
        
        # correct wrongly classified salads removing actual value       
        if not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["CARPACCIO_TECH_TERMS"]):  
            df.at[index, "technique"]  = conf["TECHNIQUES_CATEGORIES"][0].lower()  # carpaccio
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["EGOSI_TECH_TERMS"]):
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][1].lower()  # egosi
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["ENTSALADA_TECH_TERMS"]):                              
            if any(term.lower() in row['recipe_new'].lower() for term in ["legatz"]):
                if row['recipe_new'].lower() == "legatz_kokotea_labean":
                    df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][9].lower()  # labekatu
                elif row['recipe_new'].lower() == "legatz_betea":
                    df.at[index, "technique"] = "betea"  # betea
                elif row['recipe_new'].lower() == "bakailao_edo_legatz_kroketak":
                    df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][5].lower()  # frijitu
                else:
                    df.at[index, "technique"] = None
            else: 
                df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][2].lower()  # entsalada
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["ERREGOSI_TECH_TERMS"]):  
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][4].lower()  # erregosi
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["FRIJITU_TECH_TERMS"]):
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][5].lower()  # frijitu
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["KONFITATU_TECH_TERMS"]):  
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][7].lower()  # konfitatu
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["KREMAK_TECH_TERMS"]):  
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][8].lower()  # kremak
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["LABEKATU_TECH_TERMS"]):  
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][9].lower()  # labekatu
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["MARIAN_TECH_TERMS"]):  
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][10].lower()  # marian   
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["PLANTXAN_TECH_TERMS"]):
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][11].lower()  # plantxan 
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["SUEZTITU_TECH_TERMS"]):  
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][12].lower()  # sueztitu
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["ZOPAK_TECH_TERMS"]):
            df.at[index, "technique"] = conf["TECHNIQUES_CATEGORIES"][13].lower()  # zopak   
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["BETEA_TECH_TERMS"]):
            df.at[index, "technique"] = "betea"  # betea
        elif not tech and any(term.lower() in row['recipe_new'].lower() for term in conf["HOTZA_TECH_TERMS"]):
            df.at[index, "technique"] = "hotza"  # hotza
    
    return df


def complete_origin(df1, conf):
    """
    Completes the 'origin' column in the DataFrame by assigning the appropriate origin based on the recipe names 
    and predefined origin categories. The function checks the recipe name for terms that match specific origin 
    subcategories and assigns the corresponding origin.

    Parameters:
        df1 (DataFrame): A pandas DataFrame containing recipe data, with columns such as 'recipe' and 'origin'.
        conf (dict): A dictionary containing origin subcategories for different origins, with keys like 
                     "ORIGIN_ITALY", "ORIGIN_ASIA", etc., and values being lists of terms to match in the recipe names.

    Returns:
        DataFrame: The updated DataFrame with completed 'origin' columns for all recipes.
    """
    df = df1.copy()
    df.loc[:, "origin"] = None
    for index, row in df.iterrows():
        org = row['origin']
        
        # Check for various origin categories and assign corresponding origin
        if not org and any(term.lower() in row['recipe_new'].lower() for term in conf["ORIGIN_ITALIA"]):
            df.at[index, "origin"] = conf["ORIGIN_CATEGORIES"][0].lower()  # Italia
        elif not org and any(term.lower() in row['recipe_new'].lower() for term in conf["ORIGIN_ASIA"]):
            df.at[index, "origin"] = conf["ORIGIN_CATEGORIES"][1].lower()  # Asia
        elif not org and any(term.lower() in row['recipe_new'].lower() for term in conf["ORIGIN_FRANTZIA"]):
            df.at[index, "origin"] = conf["ORIGIN_CATEGORIES"][2].lower()  # Frantzia
        elif not org and any(term.lower() in row['recipe_new'].lower() for term in conf["ORIGIN_EUROPA"]):
            df.at[index, "origin"] = conf["ORIGIN_CATEGORIES"][3].lower()  # Europa
        elif not org and any(term.lower() in row['recipe_new'].lower() for term in conf["ORIGIN_MEXIKO"]):
            df.at[index, "origin"] = conf["ORIGIN_CATEGORIES"][4].lower()  # Mexiko
        elif not org and any(term.lower() in row['recipe_new'].lower() for term in conf["ORIGIN_AFRIKA"]):
            df.at[index, "origin"] = conf["ORIGIN_CATEGORIES"][5].lower()  # Afrika
        elif not org and any(term.lower() in row['recipe_new'].lower() for term in conf["ORIGIN_ESPAINIA"]):
            df.at[index, "origin"] = conf["ORIGIN_CATEGORIES"][6].lower()  # Espainia
        elif not org and any(term.lower() in row['recipe_new'].lower() for term in conf["ORIGIN_BERTAKOA"]):
            df.at[index, "origin"] = conf["ORIGIN_CATEGORIES"][7].lower()  # Bertakoa
      
    return df


def count_empty_tech_and_origin(df):
    """
    Counts the recipes that have neither a technique nor an origin specified in the DataFrame.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data, with 'technique' and 'origin' columns.

    Returns:
        tuple: A tuple where the first element is a list of recipe titles with neither technique nor origin,
               and the second element is the count of recipes with neither technique nor origin.
    """   
    no_tech_org = []   
    for index, row in df.iterrows():
        if not row["technique"] and not row["origin"]:
            no_tech_org.append(row["recipe_new"])
    return no_tech_org, len(no_tech_org)

def replace_recipe_words(df1, column, replace_dict):
    """
    Replaces values in the specified column of a DataFrame
    according to a given dictionary.
    
    :param df: Pandas DataFrame.
    :param column: Name of the column to modify.
    :param replace_dict: Dictionary with replacements.
    :return: DataFrame with the modified column.
    """
    df = df1.copy()
    df.loc[:, column] = df[column].replace(replace_dict, regex=True)
    return df

def obtain_nowanted_terms(conf):
    """
    Extracts unwanted terms from a given configuration dictionary.
    
    :param conf: Dictionary containing configuration settings.
    :return: List of unwanted words in lowercase.
    """
    no_liked_keys = [k for k in conf.keys() if k.endswith("TERMS") or k.endswith("CATEGORIES") or k.endswith("ORDER") ]
    no_liked_words = []
    
    for k in no_liked_keys:
        no_liked_words.extend(item.lower() for item in conf[k])
    
    return no_liked_words

def get_recipe_ingredients(df, column, new_column, unwanted_words):
    """
    Processes a DataFrame column by removing words that contain any substring from 'unwanted_words',
    stripping trailing digits, and storing the result in a new column.
    
    :param df: Pandas DataFrame.
    :param column: Name of the column to process.
    :param new_column: Name of the new column to store filtered words.
    :param unwanted_words: List of substrings to filter out.
    :return: Modified DataFrame with the new column.
    """
    df.loc[:, new_column] = df[column].apply(lambda x: ", ".join(
        [
            re.sub(r'\d+$', '', word.lower())  # Remove trailing digits
            for word in x.split("_")
            if not any(unwanted in word.lower() for unwanted in unwanted_words)  # Remove if contains unwanted substring
        ]
    ))
    
    return df

def remove_suffixes(df, column, suffixes):
    """
    Removes specified suffixes from words in a given DataFrame column.
    
    :param df: Pandas DataFrame.
    :param column: Name of the column containing comma-separated words.
    :param suffixes: List of suffixes to remove.
    :return: Modified DataFrame with cleaned words in the same column.
    """
    pattern = re.compile(rf"({'|'.join(map(re.escape, suffixes))})$")
    
    df[column] = df[column].apply(lambda x: ", ".join(
        [pattern.sub('', word.strip()) for word in x.split(",")] if pd.notna(x) else ""
    ))
    
    return df