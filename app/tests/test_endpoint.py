import requests

#######################################################
################ SIMPLE TEST ##########################
# curl http://127.0.0.1:8000/heartbeat
# curl http://127.0.0.1:8000/preview
#######################################################
#######################################################

def main():
    # URL of the /query endpoint (adjust the port if needed)
    url = "http://127.0.0.1:8000/query"

    # The payload with your natural language query.
    payload = {
        # examples to run...
        #"query": "Which diseases have more than 10 symptoms associated with them?"
        #"query": "What are the top 5 symptoms associated with rheumatoid arthritis?"
        #"query": "Which symptoms are associated with the common cold?"  
        #"query": "Give me an overview of amnesia"
        #"query": "What is cerebral palsy?"
        #"query": "Is asthma more common in males or females?"
        "query": "Which diseases are linked to having bladder problems?"
    }
    
    # set headers to indicate JSON content
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # raise error for bad status codes
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
    except requests.RequestException as err:
        print("Error while making request:", err)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
