# OpenGPTs

This is an open source effort to create a similar experience to OpenAI's GPTs and Assistants API.
It builds upon [LangChain](https://github.com/langchain-ai/langchain), [LangServe](https://github.com/langchain-ai/langserve) and [LangSmith](https://smith.langchain.com/).
OpenGPTs gives you more control, allowing you to configure:

- The LLM you use (choose between the 60+ that LangChain offers)
- The prompts you use (use LangSmith to debug those)
- The tools you give it (choose from LangChain's 100+ tools, or easily write your own)
- The vector database you use (choose from LangChain's 60+ vector database integrations)
- The retrieval algorithm you use
- The chat history database you use

<p align="center">
    <img alt="Configure" src="_static/configure.png" width="49%" />
    <img alt="Chat" src="_static/chat.png" width="49%" />
</p>

**Key Links**
- [GPTs: a simple hosted version](https://opengpts-example-vz4y4ooboq-uc.a.run.app/)
- [Assistants API: a getting started guide](API.md)
- [Memory: how to use long-term memory](MEMORY.md)

## Quickstart

### Start the backend

**Install requirements**

```shell
cd backend
pip install -r requirements.txt
```

**Set up persistence layer**

The backed by default uses Redis for saving agent configurations and chat message history.
In order to you use this, you need to a `REDIS_URL` variable.

```shell
export REDIS_URL=...
```

**Set up vector database**

The backend by default also uses Redis as a vector database,
although you can easily switch this out to use any of the 50+ vector databases in LangChain.
If you are using Redis as a vectorstore, the above environment variable should work
(assuming you've enabled `redissearch`)

**Set up language models**

By default, this uses OpenAI, but there are also options for Azure OpenAI and Anthropic.
If you are using those, you may need to set different environment variables.

```shell
export OPENAI_API_KEY="sk-..."
```

Other language models can be used, and in order to use them you will need to set more environment variables.
See the section below on `LLMs` for how to configure Azure OpenAI, Anthropic, and Amazon Bedrock.

**Set up tools**
By default this uses a lot of tools.
Some of these require additional environment variables.
You do not need to use any of these tools, and the environment variables are not required to spin up the app
(they are only required if that tool is called).

For a full list of environment variables to enable, see the `Tools` section below.

**Set up monitoring**

Set up [LangSmith](https://smith.langchain.com/).
This is optional, but it will help with debugging, logging, monitoring.
Sign up at the link above and then set the relevant environment variables

```shell
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY=...
```

Start the backend server

```shell
langchain serve --port=8100
```

**2. Start the frontend**

```shell
cd frontend
yarn
yarn dev
```

Navigate to [http://localhost:5173/](http://localhost:5173/) and enjoy!

## Installation and Running with Docker

This project supports a Docker-based setup, streamlining installation and execution. It automatically builds images for the frontend and backend and sets up Redis using docker-compose.

### Quick Start

1. **Clone the Repository:**  
   Obtain the project files by cloning the repository.
   ```
   git clone https://github.com/langchain-ai/opengpts.git
   cd opengpts
   ```

2. **Run with Docker Compose:**  
   In the root directory of the project, execute:
   ```
   docker compose up
   ```
   This command builds the Docker images for the frontend and backend from their respective Dockerfiles and starts all necessary services, including Redis.

3. **Access the Application:**  
   With the services running, access the frontend at [http://localhost:5173](http://localhost:5173), substituting `5173` with the designated port number.

4. **Rebuilding After Changes:**  
   If you make changes to either the frontend or backend, rebuild the Docker images to reflect these changes. Run:
   ```
   docker-compose up --build
   ```
   This command rebuilds the images with your latest changes and restarts the services.

### Note
- Ensure Docker and docker-compose are installed on your system.
- Adjust the `.env` file as required for specific environment configurations.

---

## Features

As much as possible, we are striving for feature parity with OpenAI.

- [x] Sandbox - Provides an environment to import, test, and modify existing chatbots.
  - The chatbots used are all in code, so are easily editable
- [x] Custom Actions - Define additional functionality for your chatbot using OpenAPI specifications
  - Supported by adding tools
- [x] Knowledge Files - attach additional files that your chatbot can reference
  - Upload files from the UI or API, used by Retrieval tool
- [x] Tools - Provides basic tools for web browsing, image creation, etc.
  - Basic DuckDuckGo and PythonREPL tools enabled by default
  - Image creation coming soon
- [x] Analytics - View and analyze chatbot usage data
  - Use LangSmith for this
- [x] Drafts - Save and share drafts of chatbots you're creating
  - Supports saving of configurations
- [x] Publishing - publicly distribute your completed chatbot
  - Can do by deploying via LangServe
- [x] Sharing - Set up and manage chatbot sharing
  - Can do by deploying via LangServe
- [ ] Marketplace - Search and deploy chatbots created by other users
  - Coming soon

## Repo Structure

- `frontend`: Code for the frontend
- `backend`: Code for the backend
  - `app`: LangServe code (for exposing APIs)
  - `packages`: Core logic
    - `agent-executor`: Runtime for the agent
    - `gizmo-agent`: Configuration for the agent

## Customization

The big appeal of OpenGPTs as compared to using OpenAI directly is that it is more customizable.
Specifically, you can choose which language models to use as well as more easily add custom tools.
You can also use the underlying APIs directly and build a custom UI yourself should you choose.

### LLMs

You can choose between different LLMs to use.
This takes advantage of LangChain's many integrations.
It is important to note that depending on which LLM you use, you may need to change how you are prompting it.

We have expose four agent types by default:

- "GPT 3.5 Turbo"
- "GPT 4"
- "Azure OpenAI"
- "Claude 2"

We will work to add more when we have confidence they can work well.

If you want to add your own LLM or agent configuration, or want to edit the existing ones, you can find them in `backend/packages/gizmo-agent/gizmo_agent/agent_types`

#### Claude 2

If using Claude 2, you will need to set the following environment variable:

```shell
export ANTHROPIC_API_KEY=sk-...
```

#### Azure OpenAI

If using Azure OpenAI, you will need to set the following environment variables:

```shell
export AZURE_OPENAI_API_BASE=...
export AZURE_OPENAI_API_VERSION=...
export AZURE_OPENAI_API_KEY=...
export AZURE_OPENAI_DEPLOYMENT_NAME=...
```

#### Amazon Bedrock

If using Amazon Bedrock, you either have valid credentials in `~/.aws/credentials` or set the following environment variables:

```shell
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

### Tools

One of the big benefits of having this be open source is that you can more easily add tools (directly in Python).

In practice, most teams we see define their own tools.
This is easy to do within LangChain.
See [this guide](https://python.langchain.com/docs/modules/agents/tools/custom_tools) for details on how to best do this.

If you want to use some preconfigured tools, these include:

**DuckDuckGo Search**

Search the web with [DuckDuckGo](https://pypi.org/project/duckduckgo-search/). Does not require any API keys.

**Tavily Search**

Uses the [Tavily](https://app.tavily.com/) search engine. Requires setting an environment variable:

```shell
export TAVILY_API_KEY=tvly-...
```

Sign up for an API key [here](https://app.tavily.com/).

**Tavily Search (Answer Only)**

Uses the [Tavily](https://app.tavily.com/) search engine.
This returns only the answer, no supporting evidence.
Good when you need a short response (small context windows).
Requires setting an environment variable:

```shell
export TAVILY_API_KEY=tvly-...
```

Sign up for an API key [here](https://app.tavily.com/).

**You.com Search**

Uses [You.com](https://you.com/) search, optimized responses for LLMs.
Requires setting an environment variable:

```shell
export YDC_API_KEY=...
```

Sign up for an API key [here](https://you.com/)

**SEC Filings (Kay.ai)**

Searches through SEC filings using [Kay.ai](https://www.kay.ai/).
Requires setting an environment variable:

```shell
export KAY_API_KEY=...
```

Sign up for an API key [here](https://www.kay.ai/)

**Press Releases (Kay.ai)**

Searches through press releases using [Kay.ai](https://www.kay.ai/).
Requires setting an environment variable:

```shell
export KAY_API_KEY=...
```

Sign up for an API key [here](https://www.kay.ai/)

**Arxiv**

Searches [Arxiv](https://arxiv.org/). Does not require any API keys.

**PubMed**

Searches [PubMed](https://pubmed.ncbi.nlm.nih.gov/). Does not require any API keys.

**Wikipedia**

Searches [Wikipedia](https://pypi.org/project/wikipedia/). Does not require any API keys.

## Deployment

**1. Build the frontend**

```shell
cd frontend
yarn
yarn build
```

**2. Deploy to Google Cloud Run**

You can deploy to GCP Cloud Run using the following command:

First create a `.env.gcp.yaml` file with the contents from `.env.gcp.yaml.example` and fill in the values. Then run:

```shell
gcloud run deploy opengpts --source . --port 8001 --env-vars-file .env.gcp.yaml --allow-unauthenticated --region us-central1 --min-instances 1
```
