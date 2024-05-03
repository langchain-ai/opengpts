.PHONY: start

start:
	cd backend && poetry run langgraph up -c ../langgraph.json -d ../compose.override.yml
