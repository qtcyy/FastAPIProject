import uvicorn
from fastapi import FastAPI

from controller.LLMController import LLMController
from controller.SecurityController import SecurityController

app = FastAPI()

llm_controller = LLMController()
security_controller = SecurityController()
app.include_router(llm_controller.router)
app.include_router(security_controller.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
