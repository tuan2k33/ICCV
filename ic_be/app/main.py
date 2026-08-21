import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.params import Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket

from app.core.app_status import AppStatus
from app.core.setting import settings
from app.infra.database import lifespan
from app.infra.websocket import socket_manage
from app.modules.auth.controller import auth_router, user_router
from app.modules.auth.dependencies import get_token_service
from app.modules.auth.security import TokenService
from app.modules.batch.controller import router as batch_router
from app.modules.counting_group.controller import router as counting_group
from app.modules.task.controller import router as task_router
from app.modules.tenant.controller import router as tenant_router
from app.modules.uploader.controller import blob_router
from app.utils.response import make_error_response


class Application:
    def __init__(self):
        self.app = FastAPI(lifespan=lifespan)
        self.manager = socket_manage
        self.setup_router()
        self.init_cors()
        self.add_middleware()
        self.configure_logging()
        self.add_exception_handlers()
        self.setup_websocket_router()

    def setup_router(self):
        """Define application routes here."""

        self.app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
        self.app.include_router(user_router, prefix="/api/user", tags=["user"])
        self.app.include_router(task_router, prefix="/api/task", tags=["task"])
        self.app.include_router(tenant_router, prefix="/api/tenant", tags=["tenant"])
        self.app.include_router(batch_router, prefix="/api/batch", tags=["batch"])
        self.app.include_router(counting_group, prefix="/api/counting_group", tags=["counting group"])
        self.app.include_router(blob_router, prefix="/api/blob", tags=["blob"])

    def setup_websocket_router(self):
        """Define WebSocket routes here."""

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket,
                                     token_service: TokenService = Depends(get_token_service)):
            access_token = websocket.cookies.get("access_token", None)
            token_data = token_service.validate_token(access_token)
            if not token_data:
                await websocket.close()
                return
            user_id = token_data.get('sub', '')
            await self.manager.connect(websocket, user_id)
            try:
                while True:
                    await websocket.receive_json()
            except Exception:
                self.manager.disconnect(websocket)

    def init_cors(self):
        """Set up CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.ALLOW_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @staticmethod
    def configure_logging():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s |:| %(levelname)s : %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def add_exception_handlers(self):
        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, validation_error: RequestValidationError):
            detail = validation_error.errors()[0]
            err_loc = detail.get('loc')
            err_field = err_loc[len(err_loc) - 1]
            err_msg = f"{detail.get('msg')}: {err_field}"
            return make_error_response(app_status=AppStatus.BAD_REQUEST, detail={
                "error_code": AppStatus.BAD_REQUEST.error_code,
                "message": err_msg
            })

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            return make_error_response(app_status=AppStatus.BAD_REQUEST, detail={
                "error_code": AppStatus.BAD_REQUEST.error_code,
                "message": exc.__str__()
            })

    def add_middleware(self):
        @self.app.middleware("http")
        async def cors_middleware(request, call_next):
            response = await call_next(request)
            origin = request.headers.get("origin")
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
            else:
                response.headers["Access-Control-Allow-Origin"] = "*"
            return response
        
    def start_app(self, host="0.0.0.0", port=8000):
        """Start the Uvicorn server."""
        uvicorn.run(self.app, host=host, port=port)


app_instance = Application()
app = app_instance.app

if __name__ == "__main__":
    # Run the application
    app_instance = Application()
    app_instance.start_app()
