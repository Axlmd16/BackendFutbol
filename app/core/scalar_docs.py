from fastapi import FastAPI
from fastapi.responses import HTMLResponse


def setup_scalar_docs(app: FastAPI) -> None:
    """
    Configurar Scalar como documentación alternativa
    Scalar es una alternativa moderna y elegante a Swagger UI
    """

    @app.get("/scalar", include_in_schema=False)
    async def scalar_html():
        """Documentación usando Scalar"""
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Backend Fútbol API - Scalar Docs</title>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                    }
                </style>
            </head>
            <body>
                <script
                    id="api-reference"
                    data-url="/openapi.json"
                    data-configuration='{
                        "theme": "purple",
                        "layout": "modern",
                        "darkMode": true,
                        "searchHotKey": "k",
                        "showSidebar": true,
                        "hideModels": false,
                        "hideDownloadButton": false
                    }'
                ></script>
                <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
            </body>
            </html>
            """,
            status_code=200,
        )
