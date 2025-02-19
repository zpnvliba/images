from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts.chat import ChatPromptTemplate, ChatPromptValue

if __name__ == "__main__":
    
    # 模型
    llm = ChatOpenAI(
        temperature=0.0,
        api_key='sk-0EXfWLim00ftiVLDVwMmotZOgSPi0aphLqXSBxefeIhoh44y',
        base_url='https://api.chatanywhere.tech',
        streaming=True
        )

    # 模板
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一名聊天助手，你的名字叫阿giao,每次开头都要以`一giao我类giao开头`，并且时不时的说一句`火花`"),
        ("human", "{text}"),
    ])

    # 输出解析器
    output_parser = StrOutputParser()
    
    # 管道
    chain = chat_prompt | llm | output_parser  # 三阶段管道

    # while True:
    #     # 直接传递用户输入字典（自动触发模板渲染）
    #     print(chain.invoke({"text":  input("请输入:")}))
    
    while True:
        user_input = input("\n请输入:")
        print("阿giao：", end="", flush=True)  # 🌟 流式输出前置符 
        
        # 🌟 流式响应核心代码 
        for chunk in chain.stream({"text":  user_input}):
            print(chunk, end="", flush=True)  # 逐块输出 
        print()  # 换行分隔 