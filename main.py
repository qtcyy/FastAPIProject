from fastapi import FastAPI

from controller.LLMController import LLMController

app = FastAPI()

llm_controller = LLMController()
app.include_router(llm_controller.router)
