.PHONY: start

start:
	cd backend && poetry run langgraph up -c ../langgraph.json -d ../compose.override.yml --postgres-uri 'postgres://postgres:postgres@langgraph-postgres:5432/postgres?sslmode=disable' --verbose

start-test:
	cd backend && poetry run langgraph up -c ../langgraph.json -d ../compose.override.test.yml --postgres-uri 'postgres://postgres:postgres@langgraph-postgres:5432/postgres?sslmode=disable' --verbose