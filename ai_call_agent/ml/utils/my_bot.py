import os
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI


conversation_store = {}

def math_tutor(query, call_sid):
    from os import environ


    environ["OPENAI_API_KEY"] = "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"


    template = """
    You are a creative assistant who generates compelling and engaging responses based on given text. Please provide responses following these guidelines:

    - Be creative and engaging in your responses while maintaining clarity.
    - Tailor the response in a way that aligns with the context of the text.
    - Use the text provided as the basis for a response but enhance it with creativity, clarity, and some marketing-friendly wording where relevant.
    - Keep the tone friendly, professional, and helpful.
    - Avoid unnecessary repetition and aim for brevity if appropriate.

    Example task:
    Text: {text}
    """


    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", query),
        ]
    )


    if call_sid not in conversation_store:
        memory = ConversationBufferMemory(memory_key="history", return_messages=True)
        conversation_store[call_sid] = memory
    else:
        memory = conversation_store[call_sid]


    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)


    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        verbose=False,
        memory=memory,
    )


    response = llm_chain.invoke({"text": query})


    memory.save_context({"input": query}, {"output": response['text']})

    return response['text']

def get_conversation_history(call_sid):
    if call_sid in conversation_store:
        memory = conversation_store[call_sid]
        return memory.load_memory_variables({})['history']
    else:
        return None


query = "hello i want to know about elogix"
call_sid = "CA20938424d30fd147af2a5d2b36ae9ea0"

response = math_tutor(query, call_sid)
print("Response:", response)

history = get_conversation_history(call_sid)
if history:
    for message in history:
        print(message)
else:
    print("No history found for this call_sid.")
