from dotenv import load_dotenv
import chainlit as cl

from src import Database, Agent

load_dotenv()
database = Database()
agent = Agent(database.get_sql_database(), database.get_schema())

        
@cl.on_message
async def on_message(message): 
    async with cl.Step(name="agent", language='sql') as agent_step:        
        async for response in agent.stream(message.content):
            await agent_step.stream_token(response.pretty_repr() + '\n')
            
    await agent_step.update()
    await cl.Message(content=response.content).send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)