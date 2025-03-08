# -*- coding: utf-8 -*-
"""
Created on Sat Mar  8 14:28:26 2025

@author: USUARIO
"""

import os
import pandas as pd

file_path ="C:/DATA_SCIENCE_HAIZEA/BASQUE_RECIPE_RECOMMENDATIONS_BY_LLM/tmp"
file ="similar.csv"

df = pd.read_csv(os.path.join(file_path,file))
df

#["1. Lehen platera", "2. Bigarren platera", "3. Azkenburukoa"]
options = ["0. False , 1.True"]
end_char = "q"

while True:
    print(f"PLEASE CHECK AND MARK DUPLICATE RECIPES TO REMOVE:")
    for option in options:
        print(option)
    print(f"ENTER '{end_char}' TO QUICK.")
    
    print(f"ARE: {recipe1} <-> {recipe2} SIMILAR? Select an option (0-1) or 'q' to quit:")
    if choice == end_char:
        break

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