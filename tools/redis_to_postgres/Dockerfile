FROM langchain/open-gpts:latest

RUN poetry add redis==5.0.1

COPY migrate_data.py .

# Run database schema migrations and then migrate data
ENTRYPOINT sh -c "make migrate && python migrate_data.py"