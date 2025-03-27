import requests
from langchain.prompts import PromptTemplate

def format_text_array(text_array):
    """
    Processes an array of text, ensuring that numbered items stay attached to their descriptions.
    
    Args:
        text_array (list): List of text elements.
    
    Returns:
        str: Formatted text with newline characters after each sentence.
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
        str: The translated text after processing.
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
    text = f"Ze ongi, {answer_sim} aukera aukeratzen dut, zein aukera eskaintzen dituzu?"
    return text

def get_submenu1_answers(answer_sim):
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