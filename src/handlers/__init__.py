from aiogram import Router

from .common import router as common_router
from .fallback import router as fallback_router
from .registration import router as registration_router
from .schedule import router as schedule_router
from .startup import router as start_up_router


def get_main_router():
    main_router = Router()
    main_router.include_routers(
        common_router, registration_router, schedule_router, start_up_router, fallback_router
    )

    return main_router
