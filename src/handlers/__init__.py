from aiogram import Router

from .registration import router as registration_router
from .common import router as common_router
from .schedule import router as schedule_router
#from .fallback import router
#from .schedule import router
#from .service import router
#from .startup import router


def get_main_router():
    main_router = Router()
    main_router.include_routers(common_router, registration_router, schedule_router)

    return main_router


