# BASQUE_RECIPE_RAG_PROTOTYPE

-   **Author**: Haizea Rumayor Lazkano
-   **Last update**: April 2025

------------------------------------------------------------------------

This GitHub project serves as a prototype for interacting with a large language model (LLM) prompt, applying **retrieval-augmented generation (RAG)** to query and provide insights from a curated Basque recipe database.

## Overview

This project utilizes **web scraping** to gather data on traditional Basque recipes from [Sukaldaritza Liburua](https://eu.wikibooks.org/wiki/Sukaldaritza_liburua/Azala). The collected data undergoes a **preprocessing** and **Natural Language Processing (NLP)** pipeline, resulting in the creation of a **relational database** for efficient data storage and retrieval.

The project incorporates a **conversation simulation models** based on the **Llama 3.2:1B** large language model, enabling users to interact in **Euskera** and retrieve contextually relevant recipe information through **retrieval-augmented generation (RAG)**.


## Key Features

- **Web Scraping**: Extracts data from online sources about traditional Basque recipes.
- **Data Preprocessing & NLP**: Cleans and processes the scraped data to make it suitable for querying.
- **Relational Database**: Structures the data into a relational database for efficient access and querying.
- **Conversation Simulation**: Implements an Ollama-based chatbot model that understands and responds in Euskera.
- **Retrieval-Augmented Generation (RAG)**: Enhances responses by querying the database for relevant recipe information during conversations.

## Project Structure

The project is organized into the following main directories and files:

- **src/**: Contains the main Python scripts for each project step.
  - `1-get_recipes_data.py`: Script for web scraping Basque recipes.
  - `2-create_database.py`: Script for creating the relational database from the scraped data.
  And two Jupyter notebooks for the LLM-RAG iteration process: 
     - `3.1-conversation_sim1_[SQL_RAG].ipynb`
     - `3.2-conversation_sim2_[SQL_RAG].ipynb`

- **modules/**: Contains reusable function modules used across different steps.
  - `get_data_functions.py`: Functions to support the data collection process.
  - `database_functions.py`: Functions to assist in database creation and management.
  - `llm_database_iteration_functions.py`: Functions for iterating with the LLM and the database.
  - `llm_iteration_functions.py`: Functions for managing LLM interactions.

- **data/**: Stores the final processed data and relational database.  
- **data_tmp/**: Temporary storage for intermediate results during the web scraping step.
- **config.yaml**: Configuration file containing project settings.
- **Dockerfile**: Docker configuration file for containerizing the application.
- **requirements.txt**: List of Python dependencies for the project.
- **run_ollama.sh**: Shell script to start Ollama 
- **supervisord.conf**: Configuration file for supervising the execution of Ollama and Jupyter notebook processes simultaneously.


## Installation and Run Steps

To get started with this project, please follow these steps:

### Prerequisites

1. **Install Docker**: Ensure Docker is installed on your machine. You can download and install it from the [Docker website](https://www.docker.com/products/docker-desktop).

### Building and Running the Docker Image

1. **Navigate to the Project Directory**:
Open your terminal and navigate to the root directory of the project where the `Dockerfile` is located.

2. **Build the Docker Image**:

Run the following command to build the Docker image. Replace `<app>` with the desired application name:

   ```bash
   docker build -t <app> .
   ```

3. **Run the Docker Image**:

Once the image is built, run the following command to start the Docker container. Replace `<app>` with the corresponding application name:

   ```bash
   docker run -it -p 11434:11434 -p 8888:8888 <app>
   ```

This will run the application and expose the necessary ports:
- Port **11434** for Ollama.
- Port **8888** for Jupyter Notebook.

After running the container, you can interact with the LLM model and Jupyter notebook as described in the project documentation.




## Project Workflow

1. **Web Scraping**:
   - The web scraping process uses the `src/1-get_recipes_data.py` script and functions from `modules/get_data_functions.py`.
   - The scraped data is processed in multiple steps and stored in the `data_tmp/` folder.

2. **Database Creation**:
   - The database creation is handled by the `src/2-create_database.py` script, which utilizes functions from `modules/database_functions.py`.
   - The final database is saved in the `data/` folder.

3. **LLM-RAG Iteration**:
 
   - These notebooks use functions from `modules/llm_database_iteration_functions.py` and `modules/llm_iteration_functions.py` to enable the LLM to interact with the database using retrieval-augmented generation (RAG).
