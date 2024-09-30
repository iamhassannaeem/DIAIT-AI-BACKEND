
# import os

# # Set environment variable
# os.environ['OPENAI_API_KEY'] = "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"





# from openai import OpenAI

# client = OpenAI()

# stream = client.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[{"role": "user", "content": "Say this is a test"}],
#     stream=True,
# )
# for chunk in stream:
#     if chunk.choices[0].delta.content is not None:
#         print(chunk.choices[0].delta.content, end="")



#pip install langchain
# pip install langchain_openai




from os import environ
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chains import LLMChain 
from langchain.chains import ConversationChain
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import os
environ["OPENAI_API_KEY"] = "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"


template = """
You are a helpful and concise math tutor. Please answer to the user it could be teacher or student answers accordingly.
Things you have to keep in mind are following:
    - the user will try to answer the question asked by you,
    - or a teacher might tell you that what is student curret progress.
    - if student try to ask that they do not know the specific thing, then you have to explain it to them in the easiest way.
    - Also make sure that the conversation stays on the topic, and did not get off the track.
    - If the question is other then maths assistance, try to appologise in a good manner, and dont entertain any other kind of request.
    - Also remeber to redirect the conversation towards the actual questions.
    - You should Not jump to the next question until the first question is entertained.
    - if they dont know the answer explain it to them, and ask again.
    - But you should never jump to the next question, until or unless student answer to the existing question. 
"""


prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{query}"),
        ]
    )

memory = ConversationBufferMemory(memory_key="history", return_messages=True)

memory.save_context({"input": "Hello"}, {"output": "Welcome to the circle section of AI Maths! We'll be learning about three key parts of a circle: the circumference, the radius, and the diameter. You can ask questions anytime you're unsure."})
memory.save_context({"input": "ok"}, {"output": "Let's start by identifying the circumference. Please click on the circumference line in the diagram."})




llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)


llm_chain = LLMChain(
    llm= llm,
    prompt=prompt_template,
    verbose=False,
    memory=memory,
)


while True:
    x = input("ask a question  ('_')  ")
    response = llm_chain.invoke({"query": x})
    print(response['text'])



