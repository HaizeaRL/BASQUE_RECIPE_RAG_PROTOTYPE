import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import pandas as pd


# TODO: REVISE FUNCTION COMMENT AND DESCRITIONS

def scrap_recipes_titles_and_url(sub_soup, base_url):
    
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
    for key in dictionary.keys():
        for recipe in dictionary.get(key):       
            if recipe == recipe_title:
                return key

def recipes_dict_to_df(recipes, techniques_dict, order_dict ):
    recipes_tab=[]

    # Iterate over the categories and their corresponding recipes
    for ingredient, recipe_list in recipes.items():
        for recipe in recipe_list:
            for recipe_title, url in recipe.items():
                
                technique = find_category_by_recipe (techniques_dict , recipe_title)
                dish_order = find_category_by_recipe (order_dict , recipe_title)
                
                # todo add url
                recipes_tab.append({"Ingredient": ingredient, "Order":dish_order,
                                    "Technique":technique,  "Title":recipe_title,
                                    "Url": url})
    
    # convert table to df
    return pd.DataFrame(recipes_tab)

def group_titles_with_ingredients(df):
    # Group by 'Title' and aggregate:
    grouped_df = (df.groupby('Title', as_index=False)
                    .agg({
                        "Ingredient": list, 
                        "Order": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "Technique": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "Url": list
                    }))
    return grouped_df


def complete_dish_order(df):
    no_order = []
    for index, row in df.iterrows():
        ingredient = row['Ingredient']
        dish_order = row['Order']
        title = row['Title']
        if not dish_order and any(ing in ["Arraina", "Haragia", "Barraskiloak", "Itsaskia"] for ing in ingredient):
            row["Order"] = ["Bigarren platerak"]
        elif not dish_order and any(ing in ["Arroza", "Pasta", "Lekaleak", "Barazkia"] for ing in ingredient):                
            row["Order"] = ["Lehen platerak"]
        elif not dish_order and any(ing in ["Esnekiak", "Fruta",  "Txokolatea"] for ing in ingredient):
            # correct: Guakamole
            if any(term in row['Title'] for term in ["Guakamole"]):
                row["Order"] = ["Lehen platerak"]            
            # correct: Eperrak txokolate saltsan
            if any(term in row['Title'] for term in ["saltsan"]):
                row["Order"] = ["Bigarren platerak"]                
            row["Order"] = ["Azkenburukoak"]
        elif dish_order and any(ing in ["Barazkia"] for ing in ingredient):
            # correct: Barazki eta txekor azpizun erregosia
            if any(term in row['Title'] for term in ["erregosi"]):
                row["Order"] = ["Bigarren platerak"]  
        elif not dish_order:
            no_order.append(title)
    return no_order

def view_recipes_by_category (recipe_df, field, category):
    print(category.upper())
    for index, row in recipe_df.iterrows():    
        if  row[field]  ==   category:
            print(row["Title"])

def ask_for_dish_menu_order(recipe):
    options = ["1. Lehen platera", "2. Bigarren platera", "3. Azkenburukoa"]
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
                return ["Lehen platerak"]
            elif int(choice) == 2:
                return ["Bigarren platerak"]
            else:
                return ["Azkenburukoak"]
        else:
            print("Invalid choice! Please enter 1, 2, or 3.")

def complete_dish_order_by_user(recipe_df, no_order_list):
    for index, row in recipe_df.iterrows():
        if row['Title'] in no_order_list:
            row["Order"] = ask_for_dish_menu_order(row['Title'])

def ask_for_recipes_by_order(recipe_df):

    no_order = complete_dish_order(recipe_df)
    if len(no_order) == 0:
        print("\nAll recipes has dish order")

    options = ["1. Lehen platerak", "2. Bigarren platerak", "3. Azkenburukoak"]
    end_char = "q"

    while True:
        print(f"\nWhich recipes you want to see? ")
        for option in options:
            print(option)
        print(f"Enter '{end_char}' to quit.")

        choice = input("Select an option (1-3) or 'q' to quit: ").strip()

        if choice == end_char:
            break
        elif choice in ["1", "2", "3"]:
            if int(choice) == 1:
                view_recipes_by_category(recipe_df, "Order", "Lehen platerak")
            elif int(choice) == 2:
                view_recipes_by_category(recipe_df, "Order", "Bigarren platerak")
            else:
                view_recipes_by_category(recipe_df, "Order", "Azkenburukoak")
        else:
            print("Invalid choice! Please enter 1, 2, or 3.")

