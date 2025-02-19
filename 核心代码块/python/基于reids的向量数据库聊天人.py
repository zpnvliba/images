# # 从csv中加载内容
# from langchain_community.document_loaders.csv_loader import CSVLoader
# from langchain_openai import OpenAIEmbeddings
# from langchain_community.vectorstores import Redis

# loader = CSVLoader('./file/random_data.csv', encoding='utf-8')
# documents = loader.load()

# # 调用分词api将分词后的内容保存到redis中


# embeddings = OpenAIEmbeddings(
#                                 model="text-embedding-3-large", 
#                                 api_key="sk-0EXfWLim00ftiVLDVwMmotZOgSPi0aphLqXSBxefeIhoh44y",
#                                 base_url='https://api.chatanywhere.tech'
#                             )

# # 3. 连接到Redis（请修改为您的配置）
# REDIS_URL = "redis://localhost:6379"

# # 4. 将文档存入Redis向量数据库
# vectorstore = Redis.from_documents(
#     documents=documents,
#     embedding=embeddings,
#     redis_url=REDIS_URL,
#     index_name="csv_data",
#     index_schema={
#         "text": [{"name": "content"}],

#         "vector": [{"name": "content_vector", "dims": 3072, "algorithm": "HNSW"}]
#     }
# )

# print("数据成功存入Redis，索引名称：", vectorstore.index_name)



# # if __name__ == "__main__":
# #     # 查询测试
# #     results = vectorstore.similarity_search("陈秀英", k=3)
# #     print("相似结果：", results)

# 上面的代码是将数据存入到redis中，下面的代码是根据这个redis数据充当数据库进行检索


# ####################################################################################################################


from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Redis
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


# 初始化embedding模型（需要与存储时一致）
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key="sk-0EXfWLim00ftiVLDVwMmotZOgSPi0aphLqXSBxefeIhoh44y",
    base_url='https://api.chatanywhere.tech'
)


# 初始化大语言模型
llm = ChatOpenAI(
        temperature=0.0,
        api_key='sk-0EXfWLim00ftiVLDVwMmotZOgSPi0aphLqXSBxefeIhoh44y',
        base_url='https://api.chatanywhere.tech',
        streaming=True
        )

# Redis连接配置（需与存储时一致）
REDIS_URL = "redis://localhost:6379"
INDEX_NAME = "csv_data"

# 连接到已存在的Redis向量库
vectorstore = Redis(
    redis_url=REDIS_URL,
    index_name=INDEX_NAME,
    embedding=embeddings
)

# 自定义提示模板
PROMPT_TEMPLATE = """请根据以下上下文信息回答问题。
如果你不知道答案或上下文信息不足，请如实回答你不知道。
上下文：{context}
问题：{question}
请用中文提供清晰、简洁的回答："""


# 创建检索增强生成链
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    chain_type_kwargs={
        "prompt": PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
    },
    return_source_documents=True
)

def chat_interface():
    print("数据库聊天机器人已启动！输入'exit'退出")
    while True:
        query = input("\n你的问题：")
        if query.lower() == "exit":
            print("再见！")
            break
        
        try:
            # 执行查询
            result = qa_chain.invoke({"query": query})
            
            # 显示回答
            print("\n回答：", result["result"])
            
                
        except Exception as e:
            print("出错了，请稍后再试。错误信息：", str(e))
            
            
if __name__ == "__main__":
    # # 相似度查询测试
    # query = "秀英的信息是什么"
    # results = vectorstore.similarity_search(query, k=5)
    
    # print(f"与'{query}'相似的结果：")
    # for i, doc in enumerate(results):
    #     print(f"\n结果 {i+1}:")
    #     print(f"内容: {doc.page_content}")
    #     print(f"元数据: {doc.metadata}")
    chat_interface()