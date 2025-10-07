# Text-to-SQL FastAPI Application

This project is a medical/disease database system that helps non-technical users access medical/disease information by asking questions or giving instructions in natural language. For example, a user can ask, "What are the top 5 most common symptoms associated with the common cold?" and the system uses OpenAI's GPT-4.1-nano model to translate the query to SQL, execute it against a database seeded with datasets from online sources, and return the results in human-readable form. 

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation and Setup](#installation-and-setup)
3. [Running the Application](#running-the-application)
4. [Project Structure](#project-structure)
5. [Usage](#usage)
6. [Credits](#credits)


## Prerequisites

Before starting, ensure you have the following:
1. Python 3.13
2. Homebrew (macOS only)
3. pyenv and pyenv-virtualenv for Python version and environment management

Development Environment Setup
1. Install & configure pyenv by running (for macOS)
```bash
brew install pyenv
brew install pyenv-virtualenv
```

2. Add the following to shell config file 
```bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```
Then restart terminal to apply changes. 

.env File Example
```ini
OPENAI_API_KEY=your_openai_key_here
DATABASE_URL=your_neon_postgresql_url_here
```

3. Create and activate virtual environment



## Installation and Setup
1. Download the code, activate the environment and install dependencies.
``` bash
# clone the repository
git clone https://github.com/hjiang21/chatdb.git
cd ChatDB

# set up the environment
pyenv activate chatdb

# install all dependencies
pip install -r requirements.txt

# add .env file
touch .env     # DB URL & PERSONAL API KEY MUST BE ADDED HERE
# DB URL: postgresql+asyncpg://neondb_owner:npg_3jNgksXqf0nm@ep-snowy-cherry-a4pd7pnf-pooler.us-east-1.aws.neon.tech/neondb
# Paste this link for the DB URL to access my Neon-hosted database. 
```

2. Upload tables to Neon PostgreSQL database
Go to data directory (cd data) and run the data/final_upload_postgres.py script to apply data preprocessing steps & upload tables to database. 





## Running the Application 
```bash
# run FastAPI server
cd ChatDB
make run

# open a second terminal window and begin querying
make query q="What are the symptoms associated with tuberculosis?"
make modify q="Add a 30 year old male patient with the stomach flu"
```


## Project Structure
ChatDB/
|── app/
|   |── db/               # DB session & config
|   |── llm/              # text-to-SQL & SQL-to-text LLM modules
|   |── main.py           # FastAPI application logic
|── data/                 # data csv files + processing/upload scripts
|── Makefile              # CLI interface
|── .env                  # (not committed) for DB url & API keys
|── requirements.txt      # Python dependencies




## Usage
Use custom-made make commands to query and modify the database. 
```bash
make query q="What are the names of the top 5 diseases associated with fever and cough?"
make query q="How many patients are over 55 years old?"
make modify q="Delete the patient with id p0123"
```

### Database Schema
disease(disease_id, name, overview)

symptom(symptom_id, name)

disease_symptom(disease_id, symptom_id)

patient(patient_id, age, gender, disease_id)

Schema is provided above to provide context for querying. Tables are populated using script (final_upload_postgres.py) which cleans and processes raw CSV data into structured format and uploads to Neon PostgreSQL via SQLAlchemy.


## Credits
Disease Overview dataset: Hugging Face (Shaheer14326/Disease_Symptoms_Dataset)
Patient Profile dataset: Kaggle (uploaded by John Smith) (https://www.kaggle.com/datasets/rigatoni30/patient-profile-disease-symptoms/data) 
DB Hosting: Neon.tech
LLM: OpenAI GPT-4.1-nano