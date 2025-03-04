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
            


def find_category_by_recipe (dictionary , recipe_title):
    for key in dictionary.keys():
        for recipe in dictionary.get(key):       
            if recipe == recipe_title:
                return key


def complete_dish_order(recipe_df):
    no_order = []
    for index, row in recipe_df.iterrows():
        ingredient = row['Ingredient']
        dish_order = row['Order']
        title = row['Title']
        if dish_order == None and ingredient in ["Arraina", "Haragia", "Barraskiloak", "Itsaskia"]:
            row["Order"] = "Bigarren platerak"
        elif dish_order == None and ingredient in ["Arroza", "Pasta", "Lekaleak", "Barazkia"]:
            row["Order"] = "Lehen platerak"
        elif dish_order == None and ingredient in ["Esnekiak", "Fruta",  "Txokolatea"]:
            row["Order"] = "Azkenburukoak"
        elif dish_order == None:
            no_order.append(title)
    return no_order
        

def view_recipes_by_category (recipe_df, field, category):
    print(category.upper())
    for index, row in recipe_df.iterrows():    
        if  row[field]  ==   category:
            print(row["Title"])

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


#  TODO HITZ KLABEAK TOPATU ETA HORREN ARABERA SAILKATU!!
no_tech = []
for index, row in recipe_df.iterrows():
    tech = row['Technique']
    if tech == None and any(term in row['Title'] for term in ["galdarraztatu", "egosi","uretan", 
                                                              "eskalfatua", "bainua", "lurrinekin",
                                                              "budina"]):
        print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["frijitua", "arrautzaztatua",
                                                                "arrautzeztatua", "tortilla",
                                                                "krepeak", "nahaskia"]):
        print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["papillote","labean", "bizkotxoa",
                                                                "tarta", "gailetak", "estrudela"]):
        print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["carpaccioa"]):
        print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["tartarra"]):
         print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["konfitatua"]):
        print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["krema", "kremak","purea"]):
        print(row['Title']) 
    elif tech == None and any(term in row['Title'] for term in ["sashimia"]):
           print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["sueztituak"]):
               print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["beteak", "beteriko", "betegaia",
                                                                "salteatua","beteta"]):
           print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["salda", "zopa"]):
            print(row['Title'])
    
    elif tech == None and any(term in row['Title'] for term in ["oporto erara", "boloniar erara",
                                                                "carbonara", "errioxar erara",
                                                                "asiar erara", "Pelaio erara",
                                                                "bizkaitar erara", "pil-pil erara",
                                                                "brandada", "koxkera erara",
                                                                "Marmitakoa", "hindua"]):
           print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["ozpin-olioa", "olio ozpinarekin", "ozpinarekin", "ozpinetan",
                                                                "eskabetxean","tartarra", "marinatua",
                                                                "gatzetan"]):
        print(row['Title'])
    elif tech == None and any(term in row['Title'] for term in ["saltsa","saltsan","saltsarekin",
                                                                "Roquefort gaztarekin"]):
         print(row['Title'])
    elif tech == None:
        no_tech.append(row['Title'])
    
    
    
    
    , 
                                                       "lurrunetan", "marian"
        no_tech.append(title)
        
[item for item in no_tech if ["galdarraztatu", "egosi","ur"] in no_tech]
        
        

text = "Orburuak urdaiazpiko eta arrautza galdarraztatuekin"

# Check if any term from no_tech is in the text

    selected_text = text
else:
    selected_text = None  # or an empty string if you prefer

print(selected_text)  # Output: "Orburuak urdaiazpiko e
    









teknikak = ["carpaccio", "egosi", "entsalada",
            "erre", "erregosi", "frijitu", "gisatua",
            "ketu","konfitatu", "krema", "labean",
            "bainua", "plantxan", "sueztitu", "zopa",
            "boloniar erara", "bizkaitar erara", "pil-pil", "saltsa",
            "oporto erara", "ozpin-olioa", "pelaio erara",
            "carbonara","freskoa", "asiar erara", "betea",
            "currya","tartar", "papillote", "errioxar erara",
            "txilindron", "galdarraztatua", "budin"]

no_tech = []
for index, row in recipe_df.iterrows():
    ingredient = row['Ingredient']
    tech = row['Technique']
    title = row['Title']
    
    matches = [substring for substring in teknikak if substring in title]
    if matches and tech == None:
        row['Technique'] = ', '.join(matches)
    elif tech == None:
        no_tech.append(title)
no_tech
