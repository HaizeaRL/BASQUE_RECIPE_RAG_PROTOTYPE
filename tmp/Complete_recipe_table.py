# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 11:45:06 2025
ASSIGN TO INGREDIENT RECIPE LIST TECHNIQUE AND DISH ORDER
@author: hrumayor
"""


import pandas as pd

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

recipe_df = recipes_dict_to_df(recipes, techniques_dict , order_dict)

def group_titles_with_ingredients(df):
    # Group by 'Title' and aggregate:
    grouped_df = (df.groupby('Title', as_index=False)
                    .agg({
                        "Ingredient": list, 
                        "Order": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "Technique": lambda x: sorted(set(x.dropna())),  # Unique sorted list without NaN
                        "Url": lambda x: set(x.dropna())  # Unique set without NaN
                    }))
    return grouped_df

recipe_df_grouped = group_titles_with_ingredients(recipe_df)
for index, row in recipe_df_grouped.iterrows():    
    print(f"RECIPE: {row['Title']} INGREDIENTS: {row['Ingredient']}, ORDER: {row['Order']}, TECH: {row['Technique']}")
print("Shape df: ", recipe_df_grouped.shape)


no_order = []
for index, row in recipe_df_grouped.iterrows():
    ingredient = row['Ingredient']
    dish_order = row['Order']
    title = row['Title']
    if not dish_order:
        print(title)
    print(dish_order)
    
    
    
    
    if dish_order == "" :
        print(row)
        row["Order"] = "Bigarren platerak"
    elif dish_order == None and ingredient in ["Arroza", "Pasta", "Lekaleak", "Barazkia"]:                 
        row["Order"] = "Lehen platerak"
    elif dish_order == None and ingredient in ["Esnekiak", "Fruta",  "Txokolatea"]:
        # correct: Guakamole
        if any(term in row['Title'] for term in ["Guakamole"]):
            row["Order"] = "Lehen platerak"             
        # correct: Eperrak txokolate saltsan
        if any(term in row['Title'] for term in ["saltsan"]):
            row["Order"] = "Bigarren platerak"                
        row["Order"] = "Azkenburukoak"
    elif dish_order != None and ingredient in ["Barazkia"]:
        # correct: Barazki eta txekor azpizun erregosia
        if any(term in row['Title'] for term in ["erregosi"]):
            row["Order"] = "Bigarren platerak"  
    elif dish_order == None:
        no_order.append(title)









def find_category_by_recipe (dictionary , recipe_title):
    for key in dictionary.keys():
        for recipe in dictionary.get(key):       
            if recipe == recipe_title:
                return key


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
            print(f"ERREZETA: {row['Title']} TALDEA: {row['Ingredient']}")

no_order = complete_dish_order(recipe_df)

view_recipes_by_category(recipe_df, "Order", "Bigarren platerak")
view_recipes_by_category(recipe_df, "Order", "Lehen platerak")
view_recipes_by_category(recipe_df, "Order", "Azkenburukoak")


# FIX RECIPE TITLE FROM DF '“ Tomate nahaskia'
for index, row in recipe_df.iterrows():
    if '“ ' in row['Title']:
        # correct recipe_df value
        aux = row['Title']
        row['Title'] = aux.replace('“ ',"")

# FIX FROM NO_ORDER LIST
no_order = [item.replace('“ ', "") if '“ ' in item else item for item in no_order]
print(no_order)

print("Recipes without dish order")
for recipe in no_order:
    print("- ", recipe)



def ask_for_recipes_by_order(recipe):
    options = ["1. Lehen platera", "2. Bigarren platera", "3. Azkenburukoa"]
    end_char = "q"

    while True:
        print(f"\nWhich recipes you want to see? ")
        for option in options:
            print(option)
        print(f"Enter '{end_char}' to quit.")

        choice = input("Select an option (1-3) or 'q' to quit: ").strip()

        if choice == end_char:
            print("Exiting program. Goodbye!")
            break
        elif choice in ["1", "2", "3"]:
            if int(choice) == 1:
                return "Lehen platerak"
            elif int(choice) == 2:
                return "Bigarren platerak"
            else:
                return "Azkenburukoak"
        else:
            print("Invalid choice! Please enter 1, 2, or 3.")

def complete_dish_order_by_user(recipe_df):
    for index, row in recipe_df.iterrows():
        if row['Title'] in no_order:
            row["Order"] = ask_for_dish_menu_order(row['Title'])
            

def count_empty_dish_order(df):
    no_dish_order = []   
    for index, row in df.iterrows():
        if not row["Order"]:
            no_dish_order.append(row["Title"])
    return no_dish_order, len(no_dish_order)
    
def count_empty_techniques(df):   
    no_tech = []   
    for index, row in df.iterrows():
        if not row["Technique"]:
            no_tech.append(row["Title"])
    return not_tech, len(no_tech)
        

def complete_tech_by_synonims(df, conf):   
    # complete techniques column as much as possible
    for index, row in df.iterrows():
        tech = row['Technique']
        if not tech and any(term.lower() in row['Title'].lower() for term in conf["CARPACCIO_TECH_SUBCATEGORIES"]):  
            row['Technique'] = ["Carpaccio"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["EGOSI_TECH_SUBCATEGORIES"]):
            row['Technique'] = ["Egosi"]
        elif not tech and any(term.lower() in row['Title'].lower() for term in conf["ENTSALADA_TECH_SUBCATEGORIES"]):                              
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
            row['Origin'] = ["Europa"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_EUROPE"]):
            row['Origin'] = ["Europa"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_MEXIKO"]):
            row['Origin'] = ["Mexiko"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_AFRICA"]):
            row['Origin'] = ["Afrika"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_SPAIN"]):
             row['Origin'] = ["Espainia"]
        elif not org and any(term.lower() in row['Title'].lower() for term in conf["ORIGIN_BASQUE"]):
             row['Origin'] = ["Bertako"]
      
    return df
   
    
   