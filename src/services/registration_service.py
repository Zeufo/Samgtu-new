import asyncio
from aiogram.types import Message
from loguru import logger


from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types


from sqlalchemy import select, update, delete, and_
from sqlalchemy.dialects.postgresql import insert

from sqlalchemy.ext.asyncio import AsyncSession
from database import User, Group
from database.models import AsyncSessionLocal


allowed_table = ['ИАИТ', 'ВБШ', "ИИЭГО", "ИНГТ", "ИТФ", "СПО", "СТФ", "ТЭФ", "ФАД", "ФММТ", "ФПГС", "ХТФ", "ЭТФ"]


class UserService():
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_user(self, user_id: int, course: int, faculty: str, group_id: int, last_time_active: str) -> User:
        new_user = User(user_id=user_id, course=course, faculty=faculty, group_id=group_id, last_time_active=last_time_active)

        stmt = insert(User).values(
            user_id=user_id,
            course=course,
            faculty=faculty,
            group_id=group_id,
            last_time_active=last_time_active
        )

        #if user exist set this values at...
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_={
                'course': stmt.excluded.course,
                'faculty': stmt.excluded.faculty,
                'group_id': stmt.excluded.group_id,
                'last_time_active': stmt.excluded.last_time_active
            }
        )

        await self.session.execute(stmt)
        await self.session.commit()

        return new_user


    async def get_user_group(self, user_id: int) -> int | None:
        query = select(User.group_id).where(User.user_id==user_id)
        result = await self.session.execute(query)
        
        return result.scalar_one_or_none()




                  
class GroupService():
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_id(self, group_name:str, course:int) -> int | None:
        query = select(Group.group_id).where(and_(Group.group_name==group_name, Group.course==course))
        result = await self.session.execute(query)

        return result.scalar_one_or_none()
        




class RegistartionUser(StatesGroup):
    waiting_for_faculty  = State()
    waiting_for_course = State()
    waiting_for_group = State()
    write_in_base = State()



async def welcome(message: Message, state: FSMContext) -> None:
    try:
        await message.answer("В боте включен режим антиспама. Если вам не ответили, попробуйте еще раз")
        await message.answer("Введите курс и название факультета.\nПример: 1ИАИТ 4ТЭФ")
        await state.set_state(RegistartionUser.waiting_for_faculty)
    except Exception:
        pass


#here we need to add what to do  if doesnt worked
async def get_user_faculty_service(message: Message, state: FSMContext) -> None:
    try:
        course = message.text
        faculty = message.text


        if course and faculty:
            faculty = faculty.lstrip("0123456789-–").upper().replace(' ', '') 
            course = course [:1]
            
            await state.update_data(faculty = faculty)
            await state.update_data(course = course)
            await message.answer("Введите название группы (105|310/ИС)")
            await state.set_state(RegistartionUser.waiting_for_group)
        
        else:
            await message.answer("Что-то пошло не так, попробуйте еще раз")
            await state.clear()

    except Exception:
        pass



async def get_user_group_service(message: Message, state: FSMContext) -> None:
    try:
        grp_name = message.text

        if grp_name:
            raw_name = grp_name

            grp_name = grp_name.upper().replace(" ", "")
            grp_name = grp_name.replace("/", '').replace('–', '').replace('-', '')

            await state.update_data(group = grp_name)  
            data = await state.get_data()

            await message.answer(f"Ваш факультет {data.get("faculty")}, Курс {data.get("course")}, группа {raw_name}")    
            #await message.answer("Все верно?", reply_markup = admit_decline_kb.as_markup(resize_keyboard=True))

            await state.set_state(RegistartionUser.write_in_base)

    except Exception:
        pass



async def write_user_service(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        text = message.text
        UserServ = UserService(session)
        GroupServ = GroupService(session)
        

        if text and text.upper() == "ДА":
            data = await state.get_data()  
            faculty = str(data.get('faculty', 0))
            course = int(data.get('course', 0))


            if faculty not in allowed_table:
                await message.answer("Факультет не найден, доступные:")
                #await message.answer(str(allowed_table), reply_markup=ReplyKeyboardRemove())
                await message.answer("/start")
                await state.clear()


            group_name = (faculty + data.get('group', 0))

            group_id = await GroupServ.get_id(group_name, course)
        
            if group_id is None:
                await message.answer("Не найдена информация о группе, проверьте данные")
                return

            user = await UserServ.add_user(message.chat.id, course, faculty, group_id, 'Not now')#type: ignore
            logger.info(f"logged succesfully with {course}\t{faculty}\t{group_id}")#kjdsbngkjsdhfgkjsadhfgkhjsahdfhkjggsajhgfjhasdgfjhksadgfjhgasdjhfgjhakdsfgj
            logger.info(f"logged succesfully with {user}")#kjdsbngkjsdhfgkjsadhfgkhjsahdfhkjggsajhgfjhasdgfjhksadgfjhgasdjhfgjhakdsfgj
            await message.answer("Можете пользоваться ботом") 

        #await message.answer("Попробуйте еще раз, проверьте название группы", reply_markup=ReplyKeyboardRemove())
        await message.answer('/start')
        await state.clear()
        return

    except Exception as e:
        logger.exception('Problem with registration', e)
        await message.answer("Что-то пошло не так, попробуйте еще раз")
        await state.clear() 



   






