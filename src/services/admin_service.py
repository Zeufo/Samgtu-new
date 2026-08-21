from services.service_classes import UserService


async def count_active_users() -> int:
    users = await UserService.count_all_users()
    return users
