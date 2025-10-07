import openai
import asyncio
from app.config import OPENAI_API_KEY
import re


def generate_summary_query(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in the environment.")
    openai.api_key = OPENAI_API_KEY

                            # receives structured data and returns a human-readable summary of the data.
    content_description =   "You are a helpful assistant that receives structured data and presents it into a human-readable format. \
                            When asked to provided descriptions or overviews, do not exceed 4 sentences. You may summarize the information to meet this limit. \
                            You must return list items (such as the names of symptoms, diseases, and/or ids) in sentence format. \
                            When describing tabular results, include all fields provided — do not drop or skip any columns. \
                            For example, if the results include both 'patient_id' and 'disease name', include both in your summary. \
                            You must only use information returned by the SQL query, do not add additional information, interpretation, or advice. \
                            Do not add sentences that don't directly describe the results. The response should exactly reflect the SQL query result, no more, no less. \
                            If no results are found, explain that you don't currently have the data available to answer that question. \
                            Do not begin responses with phrases like \'The data shows...\', just return the results of the query in readable form."
    response = openai.ChatCompletion.create(
        model="gpt-4.1-nano",
        messages=[          # Always summarize, do not simply return the structured data.
            {"role": "system", "content": content_description},
            {"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=200)
        
    summary_query = response["choices"][0]["message"]["content"].strip()

    # remove markdown formatting if present
    if summary_query.startswith("```") and summary_query.endswith("```"):
        summary_query = "\n".join(summary_query.splitlines()[1:-1]).strip()
    try:
        summary_query = summary_query.replace("\n\n", "")
        summary_query = re.sub(r'"([a-zA-Z\s]+)"', r'\1', summary_query)
    except: 
        summary_query = summary_query
    return summary_query


# async def get_text_response(prompt) -> str:
#     # Run the blocking API call in a separate thread.
#     summary_query = await asyncio.to_thread(generate_summary_query, prompt)
#     #print("GENERATED SUMMARY:", summary_query)
#     return summary_query

async def get_text_response(prompt) -> str:
    try:
        summary_query = await asyncio.to_thread(generate_summary_query, prompt)
        return summary_query
    except openai.error.RateLimitError as e:
        # Specifically catch token-per-minute issues
        if "tokens per min" in str(e):
            return "Sorry, your question is too broad or complex for me to process. Try asking something more specific."
        raise e
    except openai.error.OpenAIError as e:
        return f"Error with the LLM: {str(e)}"