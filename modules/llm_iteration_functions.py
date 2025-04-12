import requests
from langchain.prompts import PromptTemplate
import json
import re

def format_text_array(text_array):
   """
    Function that processes an array of text, ensuring that numbered items stay attached to their descriptions. 
    The function checks each element in the array and joins a numbered item with its description if the number is at 
    the end of the element. The formatted text is returned with each sentence separated by a newline.

    Parameters:
        text_array (list): List of text elements, where each element is a string representing part of the text.

    Returns:
        str: Formatted text where each sentence is separated by a newline, with numbered items attached to their descriptions.
    """
    formatted_text = []
    i = 0

    while i < len(text_array):
        if text_array[i][-1] == '.' and text_array[i][:-1].isdigit():  # Check if it's a numbered item
            formatted_text.append(text_array[i] + " " + text_array[i + 1])  # Join with next item
            i += 2  # Skip the next item since it's already added
        else:
            formatted_text.append(text_array[i])  # Just add the item
            i += 1  # Move to the next item

    return "\n".join(formatted_text)  # Join everything with newline

def translate_text_with_Elia(text, src_lang, dst_lang, verbose = False):
    """
    Function that translates a given text from a source language to a target language using the Elia translation service.

    Parameters:
        text (str): The text to be translated.
        src_lang (str): The source language code (e.g., 'eu' for Basque).
        dst_lang (str): The target language code (e.g., 'en' for English).
        verbose (bool, optional): If True, prints the response JSON for debugging. Default is False.

    Returns:
        str: The translated text after processing, with sentences formatted and joined as a string.
    """
    # URL of the main translation page (GET request to retrieve CSRF token and cookies)
    url = "https://elia.eus/traductor"  
    
    # URL for making the POST request to get the translated text
    post_url = "https://elia.eus/ajax/translate_string"  

    # Create a session to maintain cookies
    session = requests.Session()

    # Perform the initial GET request to get cookies and the CSRF token
    response = session.get(url)
    
    # Check if the request was successful
    if response.status_code != 200:
        return f"Error fetching the page: {response.status_code}"

    # Extract the CSRF token from the cookies (this can vary depending on the HTML structure)
    csrf_token = None
    for cookie in session.cookies:
        if cookie.name == "csrftoken":  # Look for the csrf token in the cookies
            csrf_token = cookie.value
            break

    # If no CSRF token is found, return an error
    if not csrf_token:
        return "CSRF token not found."

    # Prepare the headers for the POST request, specifying content type, and referring origin
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",  # Accepting JSON response
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",  # Content type for form submission
        "X-Requested-With": "XMLHttpRequest",  # Indicate the request is an AJAX request
        "Origin": "https://elia.eus",  # Origin header (same as the website)
        "Referer": url,  # Referer header to indicate the source of the request
    }

    # Prepare the payload (data) for the POST request
    data = {
        'csrfmiddlewaretoken': csrf_token,  # CSRF token to prevent cross-site request forgery
        'source_language': src_lang,  # Source language code (e.g., 'eu' for Basque)
        'input_text': text,  # The text to be translated
        'translation_engine': '1',  # The translation engine (usually a default value)
        'target_language': dst_lang,  # Target language code (e.g., 'es' for Spanish)
        'translation_model': 'general',  # The translation model (e.g., 'general' translation)
        'target_voice': 'F',  # Voice for the target language, 'F' for female and 'M' for male
    }

    # Perform the POST request to get the translated text
    response = session.post(post_url, data=data, headers=headers)
    
    # Check if the POST request was successful
    if response.status_code == 200:
        result = response.json()  # Parse the response as json     
        if verbose:
            print(result)
        return format_text_array(result['translated_sentences']) #get translated sentences and compound string
    else:
        return f"Error translating: {response.status_code}"  # Return an error if translation fails
    
def get_welcome_prompt():

    """
    Function that generates a welcome prompt for a virtual kitchen assistant. 
    The function creates a message in Basque, provides information about the assistant's capabilities, 
    and offers two options for the user to choose from. The message is then translated into English for use with a language model.

    Parameters:
        None

    Returns:
        PromptTemplate: A template object containing the translated welcome message for the assistant.
    """

    # option context
    submenu1_context = "Kontsultatu errezeta taulak eta kategoria bakoitzeko errezeta kopuruak, baita osagaien erabilera eta ezaugarriak ere."
    submenu2_context = "Kontsultatu osagai zehatz batekin edo plater-ordena batekin egin daitezkeen errezetak, menu aukerak aztertu..."


    # create welcome message
    welcome_message = (
            "Errezeta liburu bat oinarri duen datu-base lokal bat baliatuz, sukaldean espezializatutako laguntzaile birtual bat zara.\n"
            "Labur erantzuten duzu (gehienez 100 hitz).\n"
            "Erabiltzailea kaixo batez agurtu, nor zaren eta zein funtzio daukazun azaldu.\n"   
            "Ondoren 2 aukera hauek eskaini eta erabiltzaileari bat aukeratzeko aukera eskaini:\n"
            f" 1- Informazioa kontsultatu. {submenu1_context}. \n"
            f" 2- Menu bat edo plater bat osatzen lagundu.{submenu2_context}. \n"
            
        )
    # tranlate welcome message to english for llm model
    translated_welcome_message = translate_text_with_Elia(welcome_message, "eu","en")
    
    # Create template for the welcome message
    welcome_prompt = PromptTemplate(
        template= translated_welcome_message
    )
    return welcome_prompt

def get_submenu1_prompt():
    """
    Function that generates a prompt for the first submenu of the virtual kitchen assistant. 
    The function lists several options for the user, asking them to choose one. The options are provided in Basque, 
    and the text is then translated into English for use with a language model.

    Parameters:
        None

    Returns:
        PromptTemplate: A template object containing the translated submenu prompt for the assistant.
    """
    # define submenu behavior
    submenu1 = (
        "Erabiltzaileari hainbat aukera zerrendatu eta bat aukeratzeko eskatu. Laburra izan gehienez 100 hitzekin.\n"
        "Aukerak ondorengoak dira:\n 1- Informazio taulak kontsultatu.\n 2- Informazio taula errenkada kopurua kontsultatu.\n"
        "3- Taula kategoriako errezeta kopurua kontsultatu\n 4- Errezeta gehien dituzten osagai kategoriak kontsultatu (top3).\n" 
        "5- Errezeta gutxien dituzten osagai kategoriak kontsultatu (top3).\n·"
        "6- Osagai (ingrediente) kategoriako gehien erabiltzen den osagaia zein den kontsultatu, hala nola letxuga barazkitan edo txuleta haragitan.\n"
    )
    # translate text to english
    translated_submenu1 = translate_text_with_Elia(submenu1, "eu", "en")
    
    # create submenu1 prompt
    submenu1_prompt = PromptTemplate(
        template= translated_submenu1
    )

    # return prompt
    return submenu1_prompt


def get_welcome_menu_user_answer(answer_sim):
    """
    Function that generates a message based on the user's choice in the welcome menu. 
    The function takes the user's selected option and creates a response asking what options are available next.

    Parameters:
        answer_sim (str): The user's chosen option from the welcome menu.

    Returns:
        str: A message in Basque confirming the user's selection and asking for further options.
    """
    text = f"Ze ongi, {answer_sim} aukera aukeratzen dut, zein aukera eskaintzen dituzu?"
    return text

def get_submenu1_answers(answer_sim):
    """
    Function that generates a response based on the user's choice in the first submenu. 
    The function takes the user's selected option and creates a message in Basque, asking for the relevant data based on that choice.

    Parameters:
        answer_sim (int): The user's chosen option from the submenu.

    Returns:
        str: A message in Basque that corresponds to the selected option, asking for specific information.
    """

    text = None 
    if answer_sim  == 1:
        text = f"{answer_sim} aukera aukeratzen dut, emaidazu informazio-taula zerrenda."
    elif answer_sim  == 2:
       text = f"{answer_sim} aukera aukeratzen dut, emaidazu informazio-taulen errenkaden kopurua."
    elif answer_sim  == 3:
       text = f"{answer_sim} aukera aukeratzen dut, emaidazu kategoria taula bakoitzeko errezeta kopurua."
    elif answer_sim  == 4:
       text = f"{answer_sim} aukera aukeratzen dut, zerrenda itzazu errezeta gehien dituzten 3 osagai-kategoriak."
    elif answer_sim  == 5:
       text = f"{answer_sim} aukera aukeratzen dut, zerrenda itzazu errezeta gutxien dituzten 3 osagai-kategoriak."
    elif answer_sim  == 6:
       text = f"{answer_sim} aukera aukeratzen dut, esaidazu osagai kategoriako zein osagai den gehien erabiltzen dena."
    return text

def get_analysis_prompt_behavior():
    """
    Function that generates a prompt for analyzing user input to determine if it is requesting a specific recipe or food preparation. 
    The function outlines the steps for analyzing the input, extracting relevant recipe information, and categorizing ingredients. 
    The result is returned in a structured JSON format.

    Parameters:
        None

    Returns:
        str: A prompt for analyzing user input and returning the analysis in a structured JSON format.
    """

    behave="""
        Analyze the following user input: {user_input}

        Your task is to determine if the input is requesting a specific recipe and extract relevant recipe information.
        Return the analysis in a structured JSON format.

        Requirements:
        1. Identify if the input is requesting a recipe
        2. Identify if the input is requesting to prepare some food
        3. Extract recipe name if present
        4. Extract food to prepare if present    
        5. Deduce typical ingredients for the recipe
        6. Categorize the ingredients

        Return your analysis in this exact JSON structure:
        {{
            "concrete_recipe_ask": boolean,
            "concrete_food_ask": boolean,
            "recipe_name": copy recipe name as string or null,
            "food_name": copy food name as string or null,
            "ingredients": array of strings,
            "ingredient_categories": array of strings
        }}

        Example input: "I want to prepare 'zurrukutuna'"
        Example output:
        {{
            "concrete_recipe_ask": true,
            "concrete_food_ask": false,
            "recipe_name": "zurrukutuna",
            "food_name": null,
            "ingredients": ["salted cod", "garlic", "bread", "olive oil"],
            "ingredient_categories": ["fish", "aromatics", "grains", "oils"]
        }}

        Example input: "I want to prepare cookies?"
        Example output:
        {{
            "concrete_recipe_ask": false,
            "concrete_food_ask": true,
            "recipe_name": null,
            "food_name": "cookie",
            "ingredients": ["flour", "sugar ", "butter","eggs"],
            "ingredient_categories": ["grains", null, "dairy", "eggs"]
        }}

        Example input: "What's the weather like today?"
        Example output:
        {{
            "concrete_recipe_ask": false,
            "concrete_food_ask": false,
            "recipe_name": null,
            "food_name": "null",
            "ingredients": [],
            "ingredient_categories": []
        }}

        Analyze this input and provide only JSON as response: {user_input}
        """
    return behave

def extract_json_as_dict_from_response(response):
    """
    Function that extracts a JSON block from a response string and parses it into a Python dictionary. 
    The function searches for a JSON block wrapped in triple backticks and returns the parsed JSON data.

    Parameters:
        response (str): The response string containing the JSON block wrapped in triple backticks.

    Returns:
        dict or None: The parsed JSON as a dictionary if extraction is successful, otherwise None if no valid JSON is found or if there is a parsing error.
    """
    # The pattern to capture the JSON block
    pattern = r"```json\n(.*?)\n```"
    
    # Search for the pattern in the response string
    match = re.search(pattern, response, re.DOTALL)
    
    # If a match is found, return the extracted JSON as a dictionary
    if match:
        json_string = match.group(1).strip()
        try:
            # Parse the JSON string into a dictionary
            json_dict = json.loads(json_string)
            return json_dict  # Return as dictionary instead of string
        except json.JSONDecodeError:
            return None
    return None