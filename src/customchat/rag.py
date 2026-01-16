from dotenv import load_dotenv
# from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import tool
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
import os
from pydantic import BaseModel, Field
from typing import Literal

from pathlib import Path

load_dotenv()

base_dir = Path().resolve()
pdf_path = base_dir / "src" / "ragtime" / "acic-abstracts-2025.pdf"

loader = PyPDFLoader(pdf_path)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=400,
    add_start_index=True,
    # These are the OpenAI native embedding API chunking defaults. I figured
    # those probably are reasonable so stick with them.
)

# Load documents and chunk them appropriately
docs = loader.load()
docs_split = text_splitter.split_documents(docs)

# Instantiate an embedding model and a vector store
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=os.environ["OPENAI_API_KEY"]
)
vector_store = InMemoryVectorStore(embeddings)

# Index all our chunked documents into the vector store
ids = vector_store.add_documents(documents=docs_split)
# To save locally as json:
# vector_store.dump(base_dir / "vs.json")
# To load:
# InMemoryVectorStore(embeddings).load(base_dir / "vs.json", embedding=embeddings)

# Create a retriever object and corresponding tool
retriever = vector_store.as_retriever(search_kwargs={"k": 20})
@tool
def retrieve_from_database(query: str) -> str:
    """
    Search ACIC/relevant causal inference conference abstracts. This tool
    should ALWAYS be invoked when asked anything about research in general,
    causal inference, statistics, experiments, or any related topics.
    """
    docs = retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])

# Initialize a response model
model = ChatOpenAI(model="gpt-5-nano")

# Generate a function that will query the provided LLM model. The query
# is attached and can be invoked by the LLM as necessary for better context.
def generate_query_or_respond(state: MessagesState):
    """
    Call the model to generate a response based on the current state.
    Given the question, it will decide to retrieve using the retriever tool,
    or simply respond to the user.
    """
    response = (
        model.bind_tools([retrieve_from_database]).invoke(state["messages"])  
    )
    return {"messages": [response]}

# Intermediate grading step (grade the responses as relevant or not)
GRADE_PROMPT = (
    "You are a grader assessing relevance of a retrieved document to a user question. \n "
    "Here is the retrieved document: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n"
    "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."
)
class GradeDocuments(BaseModel):  
    """Grade documents using a binary score for relevance check."""
    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )
grader_model = ChatOpenAI(model="gpt-4o", temperature=0)

def grade_documents(state: MessagesState) -> Literal["generate_answer", "rewrite_question"]:
    """Determine whether the retrieved documents are relevant to the question."""
    question = state["messages"][0].content
    context = state["messages"][-1].content

    prompt = GRADE_PROMPT.format(question=question, context=context)
    response = (
        grader_model
        .with_structured_output(GradeDocuments).invoke(  
            [{"role": "user", "content": prompt}]
        )
    )
    score = response.binary_score
    if score == "yes":
        return "generate_answer"
    else:
        return "rewrite_question"

# Develop the step that will rewrite the asked question if it's ill-posed
REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Generate an improved question that is concise while being well-formulated:"
)

def rewrite_question(state: MessagesState):
    """Rewrite the original user question."""
    messages = state["messages"]
    question = messages[0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [HumanMessage(content=response.content)]}

# Generate the actual response step
ANSWER_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Keep the answer concise but complete.\n"
    "Question: {question} \n"
    "Context: {context}"
)

def generate_answer(state: MessagesState):
    """Generate an answer."""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = ANSWER_PROMPT.format(question=question, context=context)
    response = model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}

# Put all these pieces together into an agentic workflow with langgraph
workflow = StateGraph(MessagesState)

## Define the nodes we will cycle between
workflow.add_node(generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retrieve_from_database]))
workflow.add_node(generate_answer)

## Define the workflow
workflow.add_edge(START, "generate_query_or_respond")
workflow.add_conditional_edges(
    "generate_query_or_respond",
    # Assess LLM decision (call `retriever_tool` tool or respond to the user)
    tools_condition,
    {
        # Translate the condition outputs to nodes in our graph
        "tools": "retrieve",
        END: END,
    },
)
workflow.add_edge("retrieve", "generate_answer")
workflow.add_edge("generate_answer", END)

## Compile
graph = workflow.compile()



###### Testing ----------------------------------------------------------------

for chunk in graph.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "List all authors that worked on anytime-valid inference in adaptive experiments",
            }
        ]
    }
):
    for node, update in chunk.items():
        print("Update from node", node)
        update["messages"][-1].pretty_print()
        print("\n\n")