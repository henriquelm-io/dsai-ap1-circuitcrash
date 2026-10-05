"""Permite rodar com: uv run python -m circuitcrash"""

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "circuitcrash.app:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("RELOAD", "1") == "1",
    )


if __name__ == "__main__":
    main()
