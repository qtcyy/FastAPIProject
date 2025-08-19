from typing import List
from pydantic import BaseModel


class BatchDeleteRequest(BaseModel):
    """
    批量删除请求体
    """
    thread_ids: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "thread_ids": [
                    "thread_1",
                    "thread_2", 
                    "thread_3"
                ]
            }
        }