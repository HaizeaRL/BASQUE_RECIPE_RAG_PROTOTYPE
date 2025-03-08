import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import pandas as pd
import itertools
import spacy
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
    Function that converts a dictionary of recipes into a pandas DataFrame, where each recipe 
    is associated with its ingredient, title, and URL. The function also applies text corrections 
    to recipe titles.

    Parameters:
        recipe_dict (dict): A dictionary where keys are ingredients and values are lists of recipes,
                            each represented by a dictionary with the recipe title as the key and the 
                            recipe URL as the value.

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
                    "order": None,  
                    "technique":  None,  
                    "origin":  None,  
                    "recipe_url": url       # Extract the recipe URL (value)
                })

    # Convert the list of dictionaries into a pandas DataFrame
    return pd.DataFrame(data)

def group_titles_with_ingredients(df):
    """
    Function that groups a DataFrame by recipe titles and aggregates associated ingredients, 
    order, technique, origin, and recipe URLs. The function ensures that the values are unique 
    and sorted within each group.

    Parameters:
        df (DataFrame): A pandas DataFrame containing recipe data with columns like 'recipe', 
                         'ingredient', 'order', 'technique', 'origin', and 'recipe_url'.

    Returns:
        DataFrame: A pandas DataFrame where each row represents a unique recipe with aggregated 
                   ingredients, order, technique, origin, and URLs.
    """
    # Group by 'recipe' and aggregate:
    grouped_df = (df.groupby('recipe', as_index=False)
                    .agg({
                        "ingredient": lambda x: list(sorted(set(x.dropna()))),  # Unique sorted list without NaN
                        "order": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "technique": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "origin": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "recipe_url": list
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
    recipe_list =  df["recipe"].tolist()
    
    # obtain recipe pairs
    return itertools.combinations(recipe_list, 2)

def calcular_similitud(frase1, frase2, spacy_model): 
    """
    Function that calculates the similarity between two phrases using a spaCy language model.

    Parameters:
        frase1 (str): The first phrase to compare.
        frase2 (str): The second phrase to compare.
        spacy_model (spacy.Language): A loaded spaCy language model that contains word vectors.

    Returns:
        float: A similarity score between 0 and 1, representing the similarity between the two phrases.

    Raises:
        ValueError: If the spaCy model does not have word vectors loaded.
    """
    # Check if the model has word vectors
    if not spacy_model.vocab.vectors:
        raise ValueError("The spaCy model does not have word vectors loaded. Use 'es_core_news_md' or 'es_core_news_lg'.")

    # Process the phrases with spaCy
    doc1 = spacy_model(frase1)
    doc2 = spacy_model(frase2)
    
    # Compute similarity between the phrases
    similarity = doc1.similarity(doc2)
    
    return similarity

def compare_recipe_words(recipe1, recipe2):
    """
    Function that compares two recipe titles by checking if they have the same number of words.

    Parameters:
        recipe1 (str): The first recipe title to compare.
        recipe2 (str): The second recipe title to compare.

    Returns:
        bool: True if both recipe titles have the same number of words, otherwise False.
    """
    # get words
    words1 = recipe1.split()
    words2 = recipe2.split()
    
    # Compare words len
    if len(words1) == len(words2):
        return True
    else:
        return False
    
def get_similar_recipe_pairs(conf, recipe_pairs, spacy_model, save_path): 
    """
    Function that calculates the similarity between recipe pairs and generates periodic reports of 
    similar pairs that meet a defined similarity threshold. The results are saved in a CSV file.

    Parameters:
        conf (dict): A dictionary containing configuration settings, such as the similarity threshold 
                     and report interval.
        recipe_pairs (iterable): An iterable containing pairs of recipe titles (tuples) to compare.
        spacy_model (spacy.Language): A loaded spaCy language model used to compute similarity between pairs.
        save_path (str): The directory path where the resulting CSV file will be saved.

    Returns:
        str: The path to the CSV file containing the similar recipe pairs.
    """
    data = []
    start_time = time.time()  # Start time for periodic reporting
    last_report_time = start_time  # To track the last time we printed the report
    
    for index, (recipe1, recipe2) in enumerate(recipe_pairs): 
        # Calculate similarity using spaCy's word vectors
        similarity = calcular_similitud(recipe1, recipe2, spacy_model)
        
        # Filter only those that exceed the threshold and has same word lenght
        if similarity > float(conf["SIMILARITY_THRESHOLD"]) and compare_recipe_words(recipe1,recipe2):
            # Add result to the list
            data.append({
                "item1": recipe1,
                "item2": recipe2,  
                "equal": None,
                "incorrect": None 
            })
            
        # Periodic report every 30 seconds
        current_time = time.time()
        if current_time - last_report_time >= int(conf["REPORT_SECONDS"]):
            print(f"Processing similarities...")
            last_report_time = current_time  # Update last report time

    # Create a DataFrame with the results
    simil_df = pd.DataFrame(data)   

    # Save the DataFrame to a CSV file
    simil_df.to_csv(save_path, index=False, encoding=conf["FILES_ENCODING"])   
    
    # Final report after processing all pairs
    print(f"Total pairs processed: {len(recipe_pairs)}. Report saved to: {save_path}")

def compare_recipes_by_scapy(conf, recipe_pairs, save_path):
   """
    Function that compares recipe pairs using a spaCy language model and generates a list of similar recipes 
    for user correction. The function loads the spaCy model, computes similarities, and returns the path to 
    the resulting file.

    Parameters:
        conf (dict): A dictionary containing configuration settings, including the spaCy model and other options.
        recipe_pairs (iterable): An iterable containing pairs of recipe titles (tuples) to compare.
        save_path (str): The directory path where the resulting file with similar recipes will be saved.
    """
   # load recently installed model
   spacy_model = spacy.load(conf["SPACY_MODEL"].split("-")[0])
   
   # get similar recipes list to correct by user
   file_path = get_similar_recipe_pairs(conf, recipe_pairs, spacy_model, save_path)  
   return file_path


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
                remove_choice = input(f"Which item should be removed? (1: '{recipe1}' / 2: '{recipe2}'): ").strip()
                if remove_choice in ['1', '2']:
                    remove_item = recipe1 if remove_choice == '1' else recipe2
                    break
                else:
                    print("Invalid input. Please enter '1' for the first recipe or '2' for the second recipe.")
            
            simil_df.at[index, "equal"] = True  # Mark as equal
            simil_df.at[index, "incorrect"] = remove_item  # Store which item should be removed
        else:
            simil_df.at[index, "equal"] = False  # Mark as not equal
            simil_df.at[index, "incorrect"] = None  # No incorrect item to remove if not equal
    
    # Save the DataFrame to a CSV file
    simil_df.to_csv(save_path, index=False, encoding=conf["FILES_ENCODING"])   
    print(f"Report saved to: {save_path}")


def scrap_recipes_titles(sub_soup, recipes):
    """
    Function that scrapes recipe titles from a given HTML soup object by searching for specific elements
    and matching titles. It returns a list of recipes that are present in the provided recipes list.

    Parameters:
        sub_soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML of the page to scrape.
        recipes (list): A list of recipe titles to check for and collect from the page.

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
                        if recipe_title in recipes:
                            recipes_list.append(recipe_title)
    return recipes_list

def scrap_recipes_by_category_list(url, base_url , category_list, recipes_list): 
    """
    Function that scrapes recipe titles categorized by specific categories from a web page.
    It fetches the main page, extracts category-specific links, then scrapes recipe titles 
    under each category and returns them in a dictionary.

    Parameters:
        url (str): The URL of the main page to scrape.
        base_url (str): The base URL to resolve relative links.
        category_list (list): A list of categories to match and extract from the page.
        recipes_list (list): A list of recipe titles to filter and include from each category.

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
                recipes_list = scrap_recipes_titles(sub_soup, recipes_list)
                # save in the dictionary
                response_dictionary[key] = recipes_list      

    return response_dictionary