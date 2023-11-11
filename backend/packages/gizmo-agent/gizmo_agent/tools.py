from enum import Enum

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import DuckDuckGoSearchRun, ArxivQueryRun
from langchain.utilities import ArxivAPIWrapper
from langchain.tools.retriever import create_retriever_tool
from langchain.retrievers.you import YouRetriever
from langchain.vectorstores.redis import RedisFilter
from langchain.retrievers import KayAiRetriever, PubMedRetriever, WikipediaRetriever
from langchain.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.tools.tavily_search import TavilySearchResults, TavilyAnswer



from gizmo_agent.ingest import vstore


class DDGInput(BaseModel):
    query: str = Field(description="search query to look up")


class ArxivInput(BaseModel):
    query: str = Field(description="search query to look up")


class PythonREPLInput(BaseModel):
    query: str = Field(description="python command to run")


RETRIEVER_DESCRIPTION = """Can be used to look up information that was uploaded to this assistant.
If the user is referencing particular files, that is often a good hint that information may be here."""


def get_retrieval_tool(assistant_id: str):
    return create_retriever_tool(
        vstore.as_retriever(
            search_kwargs={"filter": RedisFilter.tag("namespace") == assistant_id}
        ),
        "Retriever",
        RETRIEVER_DESCRIPTION,
    )
tavily_search = TavilySearchAPIWrapper()


class AvailableTools(str, Enum):
    TAVILY = "Search (Tavily)"
    TAVILY_ANSWER = "Search (short answer, Tavily)"
    RETRIEVAL = "Retrieval"
    ARXIV = "Arxiv"
    YOU_SEARCH = "You.com Search"
    SEC_FILINGS = "SEC Filings (Kay.ai)"
    PRESS_RELEASES = "Press Releases (Kay.ai)"
    PUBMED = "PubMed"
    DDG_SEARCH = "DDG Search"
    WIKIPEDIA = "Wikipedia"



TOOLS = {
    AvailableTools.DDG_SEARCH: DuckDuckGoSearchRun(args_schema=DDGInput),
    AvailableTools.ARXIV: ArxivQueryRun(api_wrapper=ArxivAPIWrapper(), args_schema=ArxivInput),
    AvailableTools.YOU_SEARCH: create_retriever_tool(
        YouRetriever(n_hits=3, n_snippets_per_hit=3),
        "you_search",
        "Searches for documents using You.com"
    ),
    AvailableTools.SEC_FILINGS: create_retriever_tool(
        KayAiRetriever.create(
            dataset_id="company", data_types=["10-K", "10-Q"], num_contexts=3
        ),
        "sec_filings_search",
        "Search for a query among SEC Filings"
    ),
    AvailableTools.PRESS_RELEASES: create_retriever_tool(
        KayAiRetriever.create(
            dataset_id="company", data_types=["PressRelease"], num_contexts=6
        ),
        "press_release_search",
        "Search for a query among press releases from US companies"
    ),
    AvailableTools.PUBMED: create_retriever_tool(
        PubMedRetriever(),
        "pub_med_search",
        "Search for a query on PubMed"
    ),
    AvailableTools.TAVILY: TavilySearchResults(api_wrapper=tavily_search),
    AvailableTools.WIKIPEDIA: create_retriever_tool(
        WikipediaRetriever(),
        "wikipedia",
        "Search for a query on Wikipedia"
    ),
    AvailableTools.TAVILY_ANSWER: TavilyAnswer(api_wrapper=tavily_search),

}

TOOL_OPTIONS = {e.value: e.value for e in AvailableTools}
