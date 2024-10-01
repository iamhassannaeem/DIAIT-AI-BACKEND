import os
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

def math_tutor(query):
    from os import environ

    # Set environment variable for OpenAI API key
    environ["OPENAI_API_KEY"] = "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"

    # Define the prompt template
    template = """
   You are a helpful and concise guide for providing weather information in Pakistan. Please answer the user’s questions based on the following guidelines:

- Provide up-to-date weather details such as temperature, humidity, wind speed, and precipitation in various regions of Pakistan.
- The user may ask about specific cities (e.g., Islamabad, Karachi, Lahore), so be prepared to offer regional details.
- If the user asks for a weather forecast, give the most recent forecast available.
- Avoid providing weather information for regions outside Pakistan unless directly asked.
- If asked an unrelated question, politely apologize and gently redirect the conversation back to weather-related topics.
- Make sure the user’s current query is fully addressed before moving on to a new question.



    """

    # Create the chat prompt template
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", query),  # Use the query directly from the function parameter
        ]
    )

    # Set up conversation memory to store context
    memory = ConversationBufferMemory(memory_key="history", return_messages=True)

    # Set up the OpenAI LLM (GPT-3.5-Turbo)
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)

    # Create the LLM chain with memory
    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        verbose=False,
        memory=memory,
    )

    # Invoke the chain with the provided query and return the response
    response = llm_chain.invoke({"query": query})
    return response['text']  # Return the response text
