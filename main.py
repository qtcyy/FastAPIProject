import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controller.LLMController import LLMController

app = FastAPI()

# 添加CORS中间件，允许所有来源的跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

llm_controller = LLMController()
app.include_router(llm_controller.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
