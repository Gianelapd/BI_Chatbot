from langchain_community.utilities.sql_database import SQLDatabase
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_core.tools import Tool
from langchain_experimental.tools import PythonAstREPLTool
from langchain import hub
import os
from dotenv import load_dotenv
from src.utils import ChatbotUtils
from src.retriever import TextRetriever


load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY is missing. Ensure it's set in the .env file.")

#prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
#system_message = prompt_template.format(dialect="PostgreSQL", top_k=6)

class Agent:
    def __init__(self, db: SQLDatabase, schema: dict):

        self.model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1, google_api_key=api_key)
        self.SQLtoolkit = SQLDatabaseToolkit(db=db, llm=self.model)
        self.pythontoolkit= Tool(
            name="python_repl",
            description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
            func=PythonAstREPLTool(),
            )       

        self.memory = MemorySaver()
        self.retriever = TextRetriever(database=db)

        self.retriever_tool = Tool(
            name="retriever_tool",
            description="Retrieves proper nouns such as company names, venue names, venue groups, and instruments from the database based on user queries.Use to look up values to filter on. Input is an approximate spelling of the proper noun, output is \
valid proper nouns. Use the noun most similar to the search term.",
            func=self.retriever.retrieval_tool,
        )

        self.graph = create_react_agent(
            self.model, 
            tools= self.SQLtoolkit.get_tools()+[self.retriever_tool,self.pythontoolkit], 
            checkpointer=self.memory,
            state_modifier=ChatbotUtils(schema=schema).get_prompt()
        )
        self.config = {"configurable": {"thread_id": "1"}}

    
    async def stream(self, user_input: str):
        inputs = dict(
            input={"messages": [("user", user_input)]},
            stream_mode="updates",
            config=self.config
        )
        async for output in self.graph.astream(**inputs):
            for key, value in output.items():
                yield value["messages"][-1]
