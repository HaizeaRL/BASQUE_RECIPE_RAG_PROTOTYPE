import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

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
        
            recipies_list = []
            
                    
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
                                recipe_url = link2.get("href")
                                
                                # Add to dictionary
                                recipe_dict = {recipe_title: recipe_url}
                                
                                # Append to the list of recipes
                                recipies_list.append(recipe_dict)
            
            # Group recipes by ingredient in a dictionary
            recipes[ingredient] = recipies_list

    # return actual ingredient list and recipes per ingredients
    return ingredients_list, recipes


        
def ask_user_to_complete_data(stop_words_url, ingredients_list, recipes):
    """
    Function that ask to the user to evaluate whether a recipe words are ingredient, ingredient subgroup or
    technique.
    
    Parameters:
        stop_words_url (str): The URL of the web with basque stop words to take into account.
        ingredients_list (list(str)): List of main ingredients achieve from the web scrapping to be completed.
        recipes (list(dict)) : List of recipes by ingredients in order to loop and complete ingredient, 
        ingredient subgroup or technique tables.

    Returns:
        subgroups_dict_list: list of subgroups relations. Arraina = atun
        ingredients_list: completes main ingredients list
        technique_list: complete with techniques: arrautzeztatu..
    """ 
    subgroups_dict_list = set()
    technique_list = set()
 
    # Fetch the stop words
    response = requests.get(stop_words_url)
    stop_words = set(response.text.splitlines())

    for key in recipes.keys():
        print("\nRecipies of:", key)
        views = set()
        for recipe_list in recipes.get(key):
            for recipe in recipe_list:
                # Your list of words
                words = recipe.split(" ")

                # Filter out stop words
                filtered_words = [word for word in words if word.lower() not in stop_words]
                
                for word in filtered_words:
                    if word not in views:
                        views.add(word)
                        while True:
                            print("---------")
                            n = input(f"Is the word '{word}' subgroup of ingredient '{key}'? (y/n): ").strip().lower()
                            if n == 'y':
                                subgroups_dict_list.add((key, word))
                                break
                            elif n == 'n':
                                while True:
                                    n = input(f"Is the word '{word}' an ingredient? (y/n): ").strip().lower()
                                    if n == 'y':
                                        ingredients_list.add(word)
                                        break
                                    elif n == 'n':
                                        while True:
                                            n = input(f"Is the word '{word}' a technique? (y/n): ").strip().lower()
                                            if n == 'y':
                                                technique_list.add(word)
                                                break
                                            elif n == 'n':
                                                break
                                            else:
                                                print("Invalid input. Please enter 'y' or 'n'.")
                                                continue
                                        break
                                    else:
                                        print("Invalid input. Please enter 'y' or 'n'.")
                                        continue
                                break
                            else:
                                print("Invalid input. Please enter 'y' or 'n'.")
                                continue
    return subgroups_dict_list, ingredients_list, technique_list 

def singularize(word):
    """
    Normalize a Basque word by singularizing it.

    Parameters:
        word (str): A word to singularize.

    Returns:
        str: The singularized form of the word.
    """
    if word.endswith("rrak"):
        # Example: "Itsas belarrak" -> "Itsas belar"
        return word[:-3]
    elif word.endswith("iak"):
        # Example: "Esnekiak" -> "Esneki"
        return word[:-3] + "i"
    elif word.endswith("oak"):
        # Example: "Onddoak" -> "Onddo"
        return word[:-2]
    elif word.endswith("eak"):
        # Example: "Lekaleak" -> "Lekale"
        return word[:-2]
    elif word.endswith("ia"):
        # Example: "Legamia" -> "Legami"
        return word[:-1]
    elif word.endswith("k"):
        # Example: "Pasak" -> "Pasa"
        return word[:-1]
    elif word.endswith("na"):
        # Example: "Arraina" -> "Arrain"
        return word[:-1]
    else:
        return word

def get_singularized_list(word_list):
    """
    Normalize a list of Basque words by singularizing each one.

    Parameters:
        word_list (list of str): A list of words to normalize.

    Returns:
        list: A list of singularized words.
    """
    # Use a set to avoid duplicate singularized words, then convert to list
    singularized_set = {singularize(word) for word in word_list}
    return list(singularized_set)