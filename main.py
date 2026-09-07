"""本地启动入口：python main.py

等价于 `uvicorn blog:app`，但免去记命令；也可 `python -m blog`。
"""
from blog import serve

if __name__ == "__main__":
    serve()
