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
            
recipe_df.iloc[125]


techniques_dict
order_dict.keys

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
