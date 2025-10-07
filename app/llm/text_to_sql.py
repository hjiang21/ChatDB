# app/llm/text_to_sql.py
import openai
import asyncio
from app.config import OPENAI_API_KEY


def generate_prompt(user_query: str) -> str:
    schema_description = (
        "We have a SQL database with the following tables:\n"
        "1. disease: disease_id (String, primary key, e.g. 'd001'), name (String), overview (Text).\n"
        "2. symptom: symptom_id (String, primary key, e.g. 's001'), name (String).\n"
        "3. disease_symptom: disease_id (ForeignKey to disease.disease_id), symptom_id (ForeignKey to symptom.symptom_id).  Links diseases and symptoms.\n"
        "4. patient: patient_id (String, primary key, e.g. 'p001'), age (Integer), gender (String), disease_id (ForeignKey to disease.disease_id).  Stores patient records.\n)"

        "Note: The same name may appear in both 'disease' and 'symptom' tables — be careful to use the correct table.\n"    # i.e. acne is a disease & a symptom
    )

    instruction = ("Translate the following natural language query into a valid SQL query "
                    "that can be executed on the above schema. The output should be pure SQL, "
                    "without any additional commentary. If filtering by names, use ILIKE for case-insensitive matching."
                    "If using GROUP BY, include only grouped or aggregated columns in SELECT." 
                    "If you need to select full rows with filtered aggregates, consider using a subquery instead.")

    prompt = f"{schema_description}\n{instruction}\n\nUser Query: {user_query}\nSQL:"
    return prompt

def generate_sql_query(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in the environment.")
    openai.api_key = OPENAI_API_KEY

    response = openai.ChatCompletion.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that translates natural language questions into SQL queries."},
            {"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=150)
    sql_query = response["choices"][0]["message"]["content"].strip()

    # remove markdown formatting if present
    if sql_query.startswith("```") and sql_query.endswith("```"):
        sql_query = "\n".join(sql_query.splitlines()[1:-1]).strip()
    return sql_query

async def get_sql_query(user_query: str) -> str:
    prompt = generate_prompt(user_query)
    # Run the blocking API call in a separate thread.
    sql_query = await asyncio.to_thread(generate_sql_query, prompt)
    #print("GENERATED SQL:", sql_query)
    return sql_query
