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


no_tech = []
for index, row in recipe_df_grouped.iterrows():
    tech = row['Technique']
    ingredient = row['Ingredient']
    if not tech and any(term.lower() in row['Title'].lower() 
                        for term in ["galdarraztatu", "egosi","uretan", "eskalfatu","budina","papillote", "lurrunetan"]):
        row['Technique'] = ["Egosi"]
    elif not tech and any(term.lower() in row['Title'].lower() 
                          for term in ["frijitu", "arrautzaztatua","arrautzeztatua", "tortilla", 
                                       "nahaskia", "kroketa","salteatu"]):
        row['Technique'] = ["Frijitu"]
    elif not tech and any(term.lower() in row['Title'].lower() 
                          for term in ["ozpin", "olio", "eskabetxean", "entsalada", "gatzetan", "marinatua",
                                       "tartar","tar-tar", "raf"]):
                          
        row['Technique'] = ["Entsalada"]
    elif not tech and any(term.lower() in row['Title'].lower() 
                          for term in ["plantxa", "parrila","zartagin","burruntzia","brotxetak","parrillan"]):
        row['Technique'] = ["Plantxan"] 
    elif not tech and any(term.lower() in row['Title'].lower() 
                          for term in ["labe", "cake", "coulant", "gaileta", "tarta", "pastel", 
                                       "bizkotxo", "opil"]):  
        row['Technique'] = ["Labekatu"]
    elif not tech and any(term.lower() in row['Title'].lower() for term in ["carpaccio"]):  
        row['Technique'] = ["Carpaccio"]
    elif not tech and any(term.lower() in row['Title'].lower() for term in ["sueztitu", "goxatu"]):  
       row['Technique'] = ["Sueztitu"]
    elif not tech and any(term.lower() in row['Title'].lower() for term in ["konfitatu"]):  
       row['Technique'] = ["Konfitatu"]
    elif not tech and any(term.lower() in row['Title'].lower() for term in ["krema", "pure"]):  
       row['Technique'] = ["Kremak"]
    elif not tech and any(term.lower() in row['Title'].lower() for term in ["bainu"]):  
        row['Technique'] = ["Marian"]   
    elif not tech and any(term.lower() in row['Title'].lower() for term in ["gisatu"]):  
         row['Technique'] = ["Erregosi"]
    elif not tech and any(term.lower() in row['Title'].lower()
                              for term in ["bete", "enpanada", "enpanadilla"]):
         row['Technique'] = ["Betea"]  
    elif not tech and any(term.lower() in row['Title'].lower()
                              for term in ["izozki", "maionesa", "marmelada", "mazedonia", "irasagar",
                                           "pintxoa"]):
          row['Technique'] = ["Hotza"]   
    elif not tech and any(term.lower() in row['Title'].lower()
                              for term in ["salda"]):
          row['Technique'] = ["Zopak"]   
    elif not tech and any(term.lower() in row['Title'].lower() 
                              for term in ["lasagna","risotoa","risottoa", "boloniar",
                                           "carbonara","tagliatel","pasta","kaneloi", 
                                           "ragout", "mozzarella","pesto", "tiramisu"]):
        row['Technique'] = ["Italiarra"]
    elif not tech and any(term.lower() in row['Title'].lower() 
                          for term in ["basmati","curry", "hindu", "txina", "asiar", "sushi",
                                       "hiru gutiziko arroza","basa arroza", "sashimia"]):
        row['Technique'] = ["Asiarra"]
    elif not tech and any(term.lower() in row['Title'].lower() 
                          for term in ["frantzia", "krep","roquefort", "tatin","mollet",
                                        "ganatxea","kanape", "panatxe","mousse"]):
        row['Technique'] = ["Frantziarra"]
    elif not tech and any(term.lower() in row['Title'].lower() for term in ["tinga","guakamole"]):
        row['Technique'] = ["Mexikarra"]
    elif not tech and any(term.lower() in row['Title'].lower() for term in ["fouti"]):
        row['Technique'] = ["Afrikarra"]
    elif not tech and any(term.lower() in row['Title'].lower() for term in ["moussaka", "estrudel", "oporto","brandada"]):
        row['Technique'] = ["Europarra"]
    elif not tech and any(term.lower() in row['Title'].lower() 
                          for term in ["andaluzia", "valentzia", "errioxa", "galizia",
                                       "fideua", "koka", "morroi","flamenka",
                                       "garbantzuak tripakiekin","patata tortila",
                                       "ganbak baratxuritan", "bijiliako Txitxirioak","boilur"]):
         row['Technique'] = ["Espainiarra"]
    elif not tech and any(term.lower() in row['Title'].lower() 
                          for term in ["tolosa","nafarroa", "tutera", "beasain", "idiazabal", "ibarra",
                                       "baserri", "betiko", "pikillo", "onddo", "perretxiko", "piperrada",
                                       "marmitako", "hegaluze", "ttoro", "tinta", "txipiroi", "txibi",
                                       "menestra", "kokotxa", "kokote", "koxkera","konpota", "sagardo",
                                       "txakolin", "pil-pil", "saltsa berdean", "albondigak",
                                       "txilindron", "saltsan","ardo","natilak","bizkai","marinel"]):
         row['Technique'] = ["Bertakoak"]
    elif not tech:
        no_tech.append(row["Title"])
    
   