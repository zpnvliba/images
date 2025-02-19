from langchain_openai import OpenAIEmbeddings

#  ChatOpenAI(
#         temperature=0.0,
#         api_key='sk-0EXfWLim00ftiVLDVwMmotZOgSPi0aphLqXSBxefeIhoh44y',
#         base_url='https://api.chatanywhere.tech',
#         streaming=True
#         )

embeddings = OpenAIEmbeddings(
                                model="text-embedding-3-large", 
                                api_key="sk-0EXfWLim00ftiVLDVwMmotZOgSPi0aphLqXSBxefeIhoh44y",
                                base_url='https://api.chatanywhere.tech'
                            )

aa = embeddings.embed_query("Hello, world!")
print(aa)
