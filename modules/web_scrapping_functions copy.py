import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import pandas as pd


# TODO: REVISE FUNCTION ORDER, COMMENTS AND DESCRITIONS

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
                                    "Technique":technique, "Origin": None, "Title":recipe_title,
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
                        "Origin": lambda x: sorted(set(x.dropna())),
                        "Url": list
                    }))
    return grouped_df

def count_empty_dish_order(df):
    no_dish_order = []   
    for index, row in df.iterrows():
        if not row["Order"]:
            no_dish_order.append(row["Title"])
    return no_dish_order, len(no_dish_order)

def complete_dish_order(df, conf):
    for index, row in df.iterrows():
        ingredient = row['Ingredient']
        dish_order = row['Order']
        title = row['Title']
        if not dish_order and any(ing in conf["INGREDIENTS_FIRST_DISH_ORDER"] for ing in ingredient):                
            row["Order"] = [conf["DISH_ORDER_CATEGORIES"][0]] # "Lehen platerak"        
        elif not dish_order and any(ing in conf["INGREDIENTS_SECOND_DISH_ORDER"] for ing in ingredient):
            row["Order"] = [conf["DISH_ORDER_CATEGORIES"][1]] # "Bigarren platerak"    
        elif not dish_order and any(ing in conf["INGREDIENTS_THIRD_DISH_ORDER"] for ing in ingredient):
            # correct: Guakamole
            if any(term in row['Title'] for term in ["Guakamole"]):
                row["Order"] = [conf["DISH_ORDER_CATEGORIES"][0]]  # "Lehen platerak"
            # correct: Eperrak txokolate saltsan
            elif any(term in row['Title'] for term in ["Eperrak"]):
                row["Order"] = [conf["DISH_ORDER_CATEGORIES"][1]]  # "Bigarren platerak"  
            else:             
                row["Order"] = [conf["DISH_ORDER_CATEGORIES"][2]] # "Azkenburukoak"
        elif dish_order and any(ing in ["Barazkia"] for ing in ingredient):
            # correct: Barazki eta txekor azpizun erregosia
            if any(term in row['Title'] for term in ["erregosi"]):
                row["Order"] = [conf["DISH_ORDER_CATEGORIES"][1]]  # "Bigarren platerak"  
        if any(term.lower() in row['Title'].lower() for term in conf["FIRST_ORDER_TERMS"]):
            # correct wrongly classified
            row["Order"] = [conf["DISH_ORDER_CATEGORIES"][0]]  # "Lehen platerak"
    return df

def ask_for_dish_menu_order(recipe, conf):
    #["1. Lehen platera", "2. Bigarren platera", "3. Azkenburukoa"]
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
                return [conf["DISH_ORDER_CATEGORIES"][0]] # "Lehen platerak"
            elif int(choice) == 2:
                return [conf["DISH_ORDER_CATEGORIES"][1]] # "Bigarren platerak"
            else:
                return [conf["DISH_ORDER_CATEGORIES"][2]] # "Azkenburukoak"
        else:
            print("Invalid choice! Please enter 1, 2, or 3.")

def complete_dish_order_by_user(recipe_df, no_order_list, conf):
    for index, row in recipe_df.iterrows():
        if row['Title'] in no_order_list:
            row["Order"] = ask_for_dish_menu_order(row['Title'], conf)
    return recipe_df

def complete_dish_order_by_synomims_and_user(df, conf):
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
    no_tech = []   
    for index, row in df.iterrows():
        if not row["Technique"]:
            no_tech.append(row["Title"])
    return no_tech, len(no_tech)

def count_empty_tech_and_origin(df):   
    no_tech_org = []   
    for index, row in df.iterrows():
        if not row["Technique"] and not row["Origin"]:
            no_tech_org.append(row["Title"])
    return no_tech_org, len(no_tech_org)

def complete_tech_by_synonims(df, conf):   
    # complete techniques column as much as possible
    for index, row in df.iterrows():
        tech = row['Technique']
        # correct wrongly classified salads removing actual value       
        if not tech and any(term.lower() in row['Title'].lower() for term in conf["CARPACCIO_TECH_SUBCATEGORIES"]):  
            row['Technique'] = ["Carpaccio"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["EGOSI_TECH_SUBCATEGORIES"]):
            row['Technique'] = ["Egosi"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["ENTSALADA_TECH_SUBCATEGORIES"]):                              
            '''if any(term.lower() in row['Title'].lower() for term in ["legatz"]):
                row['Technique'] =[]
            else: '''      
            row['Technique'] = ["Entsalada"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["ERREGOSI_TECH_SUBCATEGORIES"]):  
             row['Technique'] = ["Erregosi"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["FRIJITU_TECH_SUBCATEGORIES"]):
            row['Technique'] = ["Frijitu"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["KONFITATU_TECH_SUBCATEGORIES"]):  
            row['Technique'] = ["Konfitatu"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["KREMAK_TECH_SUBCATEGORIES"]):  
           row['Technique'] = ["Kremak"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["LABEKATU_TECH_SUBCATEGORIES"]):  
            row['Technique'] = ["Labekatu"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["MARIAN_TECH_SUBCATEGORIES"]):  
            row['Technique'] = ["Marian"]   
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["PLANTXAN_TECH_SUBCATEGORIES"]):
            row['Technique'] = ["Plantxan"] 
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["SUEZTITU_TECH_SUBCATEGORIES"]):  
             row['Technique'] = ["Sueztitu"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["ZOPAK_TECH_SUBCATEGORIES"]):
              row['Technique'] = ["Zopak"]   
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["BETEA_TECH_SUBCATEGORIES"]):
             row['Technique'] = ["Betea"]  
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["HOTZA_TECH_SUBCATEGORIES"]):
             row['Technique'] = ["Hotza"] 
    return df

def complete_origin(df, conf):   
    # complete origin columns as much as possible
    for index, row in df.iterrows():
        org = row['Origin']  
        if not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_ITALY"]):
            row['Origin'] = ["Italia"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_ASIA"]):
            row['Origin'] = ["Asia"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_FRANCE"]):
            row['Origin'] = ["Frantzia"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_EUROPE"]):
            row['Origin'] = ["Europa"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_MEXIKO"]):
            row['Origin'] = ["Mexiko"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_AFRICA"]):
            row['Origin'] = ["Afrika"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_SPAIN"]):
             row['Origin'] = ["Espainia"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_BASQUE"]):
             row['Origin'] = ["Bertakoa"]
      
    return df

def get_recipes_by_category(df, category_list, category):
    for item in category_list:
        print(f"\nRecipes of: {item.upper()}")
        # select recipes of corresponding ord_item
        recipe_list = df[df[category].apply(lambda x: item in x)]["Title"].tolist()
        # print them
        for recipe in recipe_list:
            print("- ", recipe)
        input()


def correct_capitalization(text):
    # Split the text into words
    words = text.split()
    
    # Make the first word capitalized and the rest in lowercase
    words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
    
    # Join the words back into a single string
    return words

def correct_text(text):

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