from fastapi import APIRouter
from app.api.v1.auth import endpoints

router = APIRouter()

router.add_api_route("/login", endpoints.login, methods=["POST"], name="login")
router.add_api_route(
    "/refresh", endpoints.refresh_token, methods=["POST"], name="refresh"
)
router.add_api_route("/me", endpoints.get_current_user_info, methods=["GET"], name="me")
router.add_api_route("/logout", endpoints.logout, methods=["POST"], name="logout")
