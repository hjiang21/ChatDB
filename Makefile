# Makefile

ENV_FILE := .env
APP := app.main:app
HOST := 127.0.0.1
PORT := 8000

run:
	@export $$(cat $(ENV_FILE) | xargs) && uvicorn $(APP) --host $(HOST) --port $(PORT) --reload

query:
	@curl -s -X POST http://127.0.0.1:8000/query \
		-H "Content-Type: application/json" \
		-d '{"query": "$(q)"}' | jq 

# make query q="Which diseases are linked to having bladder problems?" 
# add -r '.diseaseDB_response' after jq if only want the response itself 

modify:
	@curl -s -X POST http://127.0.0.1:8000/modify \
		-H "Content-Type: application/json" \
		-d '{"query": "$(q)"}' | jq 

# make modify q="Add a 10 year old female patient with asthma"
	
	


