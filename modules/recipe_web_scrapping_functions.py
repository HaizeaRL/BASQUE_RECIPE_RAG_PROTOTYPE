import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import pandas as pd
import itertools
import stanza
import Levenshtein
import time


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

def correct_capitalization(text):
    """
    Function that corrects the capitalization of a given text by capitalizing the first word
    and making all other words lowercase.

    Parameters:
        text (str): The input string that needs to be corrected for capitalization.

    Returns:
        str: A string where the first word is capitalized and the remaining words are in lowercase.
    """
    # Split the text into words
    words = text.split()
    
    # Make the first word capitalized and the rest in lowercase
    words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
    
    # Join the words back into a single string
    return words

def correct_text(text):
    """
    Function that performs a series of text corrections, including removing special characters, 
    correcting capitalization, and adjusting numerization of the text.

    Parameters:
        text (str): The input string that needs to be processed and corrected.

    Returns:
        str: A corrected string where special characters are removed, the first word is capitalized, 
             other words are in lowercase, and any numerization issues are addressed.
    """
    # remove special characters
    text = text.replace('"', '').replace('“', '').replace(',', '').replace('-',' ').replace("'",'').replace('.jpg','').strip()

    # correct capitalization
    words = correct_capitalization(text)
    
    # correct numerization
    if words[len(words) - 1].isdigit():  
        words[len(words) - 2] = words[len(words) - 2]+words[len(words) - 1]
        words.pop()
    
    # Join the words back into a single string
    return ' '.join(words)


def recipe_dict_into_df(recipe_dict):
    """
    Function that converts a dictionary of recipes into a pandas DataFrame, where each recipe is associated 
    with its ingredient, title, and URL. The function also applies text corrections to recipe titles.

    Parameters:
        recipe_dict (dict): A dictionary where the keys are ingredients and the values are lists of recipes.
        Each recipe is represented as a dictionary with the recipe title as the key and the recipe URL as the 
        value.

    Returns:
        DataFrame: A pandas DataFrame where each row contains the ingredient, recipe title, and recipe URL.
    """
    # List to store the data
    data = []

    # Loop through the dictionary and extract the necessary information
    for ingredient, recipe_list in recipe_dict.items():
        for recipe in recipe_list:
            # Assuming each recipe is a dictionary with a single key-value pair
            for title, url in recipe.items():  # Iterate over key-value pairs 
            
                # correct recipe title
                title = correct_text(title)                    
                            
                # Add each recipe to the data list with ingredient, title, and URL
                data.append({
                    "ingredient": ingredient,
                    "recipe": title,  # Extract the recipe title (key)
                    "recipe_url": url       # Extract the recipe URL (value)
                })

    # Convert the list of dictionaries into a pandas DataFrame
    return pd.DataFrame(data)

def group_titles_with_ingredients(df):
    """
    Function that groups a DataFrame by recipe titles and aggregates the associated ingredients, order, 
    technique, origin, and recipe URLs. The function ensures that the values are unique and sorted within 
    each group.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data with columns such as 'recipe', 'ingredient', 
        'order', 'technique', 'origin', and 'recipe_url'.

    Returns:
        DataFrame: A pandas DataFrame where each row represents a unique recipe with aggregated ingredients,
        and URLs.
    """
    # Group by 'recipe' and aggregate:
    grouped_df = (df.groupby('recipe', as_index=False)
              .agg({
                  "ingredient": lambda x: ', '.join(set(x.dropna())),
                  "recipe_url": lambda x: ', '.join(x.dropna())
              }))
    return grouped_df


def get_recipe_pairs_to_compare(df):
    """
    Function that generates all possible unique pairs of recipes from a given DataFrame.

    Parameters:
        df (DataFrame): A pandas DataFrame containing a column 'recipe' with recipe titles.

    Returns:
        iterator: An iterator that yields tuples, where each tuple contains a pair of recipe titles 
                  from the DataFrame.
    """
    # obtain recipe_list from df
    recipe_list =  df["cleaned"].tolist()
    
    # obtain recipe pairs
    return itertools.combinations(recipe_list, 2)

def calculate_similarity(recipe1, recipe2, stanza_pipeline):
    """
    Calculates the similarity between two recipe titles using a Stanza pipeline.
    The similarity is computed as a weighted combination of Jaccard and Levenshtein similarity.

    Parameters:
        recipe1 (str): The first recipe title.
        recipe2 (str): The second recipe title.
        stanza_pipeline (stanza.Pipeline): An initialized Stanza pipeline for processing text.

    Returns:
        float: The combined similarity score between the two titles.
    """
    # Process each recipe title using Stanza (tokenization, lemmatization)
    doc1 = stanza_pipeline(recipe1)
    doc2 = stanza_pipeline(recipe2)
    
    # Extract lemmas from each title
    lemmas1 = [word.lemma for sentence in doc1.sentences for word in sentence.words]
    lemmas2 = [word.lemma for sentence in doc2.sentences for word in sentence.words]
    
    # Calculate Jaccard similarity (set-based)
    set1, set2 = set(lemmas1), set(lemmas2)
    if not set1 or not set2:
        return 0.0
     
    # Jaccard similarity: intersection size divided by union size (exact coincidencies)
    jaccard_similarity = len(set1.intersection(set2)) / len(set1.union(set2))
    
    # Calculate average Levenshtein similarity between all lemmatized words (little differences )
    levenshtein_sim = 0
    for word1 in lemmas1:
        for word2 in lemmas2:
            levenshtein_sim += Levenshtein.ratio(word1, word2)
    
    # Avoid division by zero if either list is empty
    if lemmas1 and lemmas2:
        levenshtein_sim /= (len(lemmas1) * len(lemmas2))
    else:
        levenshtein_sim = 0
    
    # Combine Jaccard and Levenshtein similarity (you can adjust the weights)
    # Example: Giving equal weight to both metrics
    combined_similarity = (jaccard_similarity + levenshtein_sim) / 2
    
    return combined_similarity

    
def get_similar_recipe_pairs(conf, recipe_pairs, stanza_pipeline, save_path):
    """
    Calculates the similarity for each pair of recipe titles and saves pairs that exceed
    a defined similarity threshold to a CSV file.

    Parameters:
        conf (dict): Configuration settings (e.g., similarity threshold, report interval, encoding).
        recipe_pairs (iterable): An iterable containing tuples of recipe titles to compare.
        stanza_pipeline (stanza.Pipeline): An initialized Stanza pipeline for processing texts.
        save_path (str): The file path where the CSV with similar recipe pairs will be saved.

    """
    data = []
    start_time = time.time()
    last_report_time = start_time

    for index, (recipe1, recipe2) in enumerate(recipe_pairs):
        similarity = calculate_similarity(recipe1, recipe2, stanza_pipeline)
        
        # Filter pairs that exceed the similarity threshold and have the same word count
        if similarity > float(conf["SIMILARITY_THRESHOLD"]):
            data.append({
                "item1": recipe1,
                "item2": recipe2,
                "equal": None,
                "incorrect": None
            })
            print(f"{recipe1} <-> {recipe2}")

        # Print periodic reports every conf["REPORT_SECONDS"] seconds
        if time.time() - last_report_time >= int(conf["REPORT_SECONDS"]):
            print("Processing similarities...")
            last_report_time = time.time()

    simil_df = pd.DataFrame(data).astype({"equal": object, "incorrect": object})
    simil_df.to_csv(save_path, index=False, encoding=conf["FILES_ENCODING"])
    
def compare_recipes(conf, model_path, recipe_pairs, save_path):
    """
    Initializes a Stanza pipeline for Basque using configuration settings and compares recipe
    pairs to generate a CSV report of similar recipes.

    Parameters:
        conf (dict): Configuration settings (including STANZA_LANG and STANZA_PROCESSORS).
        model_paht: stanza model to load.
        recipe_pairs (iterable): An iterable containing tuples of recipe titles.
        save_path (str): The file path where the resulting CSV will be saved.

    Returns:
        str: The file path to the CSV with similar recipe pairs.
    """   
    # Initialize the Stanza pipeline with the specified model directory
    stanza_pipeline = stanza.Pipeline(
        lang=conf["STANZA_LANG"],
        processors=conf["STANZA_PROCESSORS"],
        model_dir=model_path
    )
    
    file_path = get_similar_recipe_pairs(conf, recipe_pairs, stanza_pipeline, save_path)
    return file_path

def remove_plural(word):
    """
    Removes specified plural suffixes from the given word.

    Parameters:
        word (str): The word from which plural suffixes will be removed.

    Returns:
        str: The word with the plural suffix removed if it ends with one of the specified suffixes; otherwise, the original word.
    """
    # List of plural suffixes to remove
    plural_suffixes = ['k', 'ar', 'rekin']

    # Iterate over each plural suffix
    for suffix in plural_suffixes:
        # If the word ends with the current suffix, remove it
        if word.endswith(suffix):
            return word[:-len(suffix)]  # Remove the plural suffix
    return word  # Return the original word if no plural suffix is found

def process_column(conf, column):
    """
    Processes a pandas Series by splitting text into words, removing unwanted words,
    applying the remove_plural function to each word, and then rejoining the words into sentences.

    Parameters:
        conf (dict): A configuration dictionary containing various settings, including a list of unwanted words.
        column (pandas.Series): A pandas Series containing text data to be processed.

    Returns:
        pandas.Series: A new Series with processed text.
    """
    # Split each string in the Series into a list of words
    words = column.str.split()

    # Remove unwanted words from each list
    filtered_words = words.apply(lambda word_list: [word for word in word_list if word not in conf.get("UNWANTED_WORDS", [])])

    # Apply the remove_plural function to each word and rejoin the words into a sentence
    return filtered_words.apply(lambda word_list: " ".join(remove_plural(word) for word in word_list))


def get_user_input_and_update(conf, simil_df, save_path):
    """
    Function that prompts the user to compare pairs of recipes and determine whether they are equal.
    The user is also asked which recipe should be removed if they are considered equal. The results are 
    then updated in the DataFrame and saved to a CSV file.

    Parameters:
        conf (dict): A dictionary containing configuration settings, including file names and encoding options.
        simil_df (DataFrame): A pandas DataFrame containing recipe pairs to compare, with columns for 'item1', 
                              'item2', 'equal', and 'incorrect'.
        save_path (str): The directory path where the updated CSV file with user input will be saved.
    """
    # Ensure 'incorrect' column can hold strings
    simil_df['incorrect'] = simil_df['incorrect'].astype(str)

    for index, row in simil_df.iterrows(): 
        recipe1 = row["item1"]
        recipe2 = row["item2"]
        
        # Ask if the items are equal
        while True:
            equal_answer = input(f"Are '{recipe1}' and '{recipe2}' equal? (y/n): ").strip().lower()
            if equal_answer in ['y', 'n']:
                break
            else:
                print("Invalid input. Please enter 'y' for yes or 'n' for no.")
        if equal_answer == 'y':
            while True:
                # Ask which item should be removed if they are equal
                remove_choice = input(f"Which item should be removed? '{recipe1}' and '{recipe2}' equal? (1/2): ").strip()
                if remove_choice in ['1', '2']:  # Check as strings first
                    remove_choice = int(remove_choice)  # Convert to integer
                    
                    if remove_choice in [1, 2]:
                        remove_item = recipe1 if remove_choice == 1 else recipe2
                        break
                    else:
                        print("Invalid input. Please enter '1' for the first recipe or '2' for the second recipe.")
                else:
                    print("Invalid input. Please enter '1' for the first recipe or '2' for the second recipe.")
            
            simil_df.at[index, "equal"] = 1  # Mark as equal
            simil_df.at[index, "incorrect"] = remove_item  # Store which item should be removed
        else:
            simil_df.at[index, "equal"] = 0  # Mark as not equal
            simil_df.at[index, "incorrect"] = None  # No incorrect item to remove if not equal

    # Save the DataFrame to a CSV file
    simil_df.to_csv(save_path, index=False, encoding=conf["FILES_ENCODING"])
    print(f"Report saved to: {save_path}")



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
        if not row["order"]:
            no_dish_order.append(row["recipe"])
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
        ingredient = [ingredient.strip() for ingredient in row['ingredient'].split(',')]
        dish_order = row['order']
        if not dish_order and any(ing in conf["INGREDIENTS_FIRST_DISH_ORDER"] for ing in ingredient):                
            df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][0] # "Lehen platerak"        
        elif not dish_order and any(ing in conf["INGREDIENTS_SECOND_DISH_ORDER"] for ing in ingredient):
            df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][1] # "Bigarren platerak"    
        elif not dish_order and any(ing in conf["INGREDIENTS_THIRD_DISH_ORDER"] for ing in ingredient):
            # correct: Guakamole
            if any(term in row['recipe'] for term in ["Guakamole"]):
                df.at[index, "order"]= conf["DISH_ORDER_CATEGORIES"][0]  # "Lehen platerak"
            # correct: Eperrak txokolate saltsan
            elif any(term in row['recipe'] for term in ["Eperrak"]):
                df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][1]  # "Bigarren platerak"  
            else:             
                df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][2] # "Azkenburukoak"
        elif dish_order and any(ing in ["Barazkia"] for ing in ingredient):
            # correct: Barazki eta txekor azpizun erregosia
            if any(term in row['recipe'] for term in ["erregosi"]):
                df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][1] # "Bigarren platerak"  
        if any(term.lower() in row['recipe'].lower() for term in conf["FIRST_ORDER_TERMS"]):
            # correct wrongly classified
            df.at[index, "order"] = conf["DISH_ORDER_CATEGORIES"][0]  # "Lehen platerak"
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
                return conf["DISH_ORDER_CATEGORIES"][0] # "Lehen platerak"
            elif int(choice) == 2:
                return conf["DISH_ORDER_CATEGORIES"][1] # "Bigarren platerak"
            else:
                return conf["DISH_ORDER_CATEGORIES"][2] # "Azkenburukoak"
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
        if row['recipe'] in no_order_list:
            row["order"] = ask_for_dish_menu_order(row['recipe'], conf)
    return recipe_df

def complete_dish_order_by_synomims_and_user(df, conf):
    """
    Completes the 'order' column in the DataFrame by first attempting to automatically assign dish orders 
    based on predefined rules and synonyms, and then prompts the user to fill in the missing orders for 
    recipes that still lack an order.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data with columns such as 'recipe' and 'order'.
        conf (dict): A dictionary containing configuration, including dish order categories and other settings.

    Returns:
        DataFrame: The updated DataFrame with completed 'order' columns for all recipes.
    """
    df1 = complete_dish_order(df, conf)
    # check if dish order is not complete yet
    no_order, without_order = count_empty_dish_order(df1)
    
    if without_order != 0:
        print(f"There are {without_order} recipes without dish order.")
        print("Lets complete asking to user.")
        # ASK USER TO COMPLETE THOSE RECIPES WITHOUT DISH ORDER
        df2 = complete_dish_order_by_user(df1, no_order, conf)         
        # check if dish order is complete 
        no_order, without_order = count_empty_dish_order(df2)
        if without_order == 0:
            print("There is no recipes without dish order")
        return df2  # Ensure df2 is returned if modified
    
    return df1  # If no modification was needed, return df1

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
            no_tech.append(row["recipe"])
    return no_tech, len(no_tech)

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
            no_tech_org.append(row["recipe"])
    return no_tech_org, len(no_tech_org)

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
        if not tech and any(term.lower() in row['recipe'].lower() for term in conf["CARPACCIO_TECH_SUBCATEGORIES"]):  
            df.at[index, "technique"]  = "Carpaccio"
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["EGOSI_TECH_SUBCATEGORIES"]):
            df.at[index, "technique"] = "Egosi"
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["ENTSALADA_TECH_SUBCATEGORIES"]):                              
            '''if any(term.lower() in row['recipe'].lower() for term in ["legatz"]):
                row['Technique'] =[]
            else: '''      
            df.at[index, "technique"] = "Entsalada"
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["ERREGOSI_TECH_SUBCATEGORIES"]):  
             df.at[index, "technique"] = "Erregosi"
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["FRIJITU_TECH_SUBCATEGORIES"]):
            df.at[index, "technique"] = "Frijitu"
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["KONFITATU_TECH_SUBCATEGORIES"]):  
            df.at[index, "technique"] = "Konfitatu"
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["KREMAK_TECH_SUBCATEGORIES"]):  
           df.at[index, "technique"] = "Kremak"
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["LABEKATU_TECH_SUBCATEGORIES"]):  
            df.at[index, "technique"] = "Labekatu"
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["MARIAN_TECH_SUBCATEGORIES"]):  
            df.at[index, "technique"] = "Marian"   
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["PLANTXAN_TECH_SUBCATEGORIES"]):
            df.at[index, "technique"] = "Plantxan" 
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["SUEZTITU_TECH_SUBCATEGORIES"]):  
            df.at[index, "technique"] = "Sueztitu"
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["ZOPAK_TECH_SUBCATEGORIES"]):
            df.at[index, "technique"] = "Zopak"   
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["BETEA_TECH_SUBCATEGORIES"]):
            df.at[index, "technique"] = "Betea"  
        elif not tech and any(term.lower() in row['recipe'].lower() for term in conf["HOTZA_TECH_SUBCATEGORIES"]):
            df.at[index, "technique"] = "Hotza" 
    return df

def complete_origin(df, conf):
    """
    Completes the 'origin' column in the DataFrame by assigning the appropriate origin based on the recipe names 
    and predefined origin categories. The function checks the recipe name for terms that match specific origin 
    subcategories and assigns the corresponding origin.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data, with columns such as 'recipe' and 'origin'.
        conf (dict): A dictionary containing origin subcategories for different origins, with keys like 
                     "ORIGIN_ITALY", "ORIGIN_ASIA", etc., and values being lists of terms to match in the recipe names.

    Returns:
        DataFrame: The updated DataFrame with completed 'origin' columns for all recipes.
    """
    df["origin"] = None
    for index, row in df.iterrows():
        org = row['origin']  
        if not org and any(term.lower() in row['recipe'].lower() for term in conf["ORIGIN_ITALY"]):
            df.at[index, "origin"] = "Italia"
        elif not org and any(term.lower() in row['recipe'].lower() for term in conf["ORIGIN_ASIA"]):
            df.at[index, "origin"] = "Asia"
        elif not org and any(term.lower() in row['recipe'].lower() for term in conf["ORIGIN_FRANCE"]):
            df.at[index, "origin"] = "Frantzia"
        elif not org and any(term.lower() in row['recipe'].lower() for term in conf["ORIGIN_EUROPE"]):
            df.at[index, "origin"]= "Europa"
        elif not org and any(term.lower() in row['recipe'].lower() for term in conf["ORIGIN_MEXIKO"]):
            df.at[index, "origin"] = "Mexiko"
        elif not org and any(term.lower() in row['recipe'].lower() for term in conf["ORIGIN_AFRICA"]):
           df.at[index, "origin"]= "Afrika"
        elif not org and any(term.lower() in row['recipe'].lower() for term in conf["ORIGIN_SPAIN"]):
            df.at[index, "origin"] = "Espainia"
        elif not org and any(term.lower() in row['recipe'].lower() for term in conf["ORIGIN_BASQUE"]):
            df.at[index, "origin"] = "Bertakoa"
      
    return df
