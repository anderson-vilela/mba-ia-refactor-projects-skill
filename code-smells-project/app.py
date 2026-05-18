from src.app import app
from src.config.settings import settings

if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://{settings.host}:{settings.port}")
    print("=" * 50)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
