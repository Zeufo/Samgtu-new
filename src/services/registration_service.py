from aiogram.types import Message
from loguru import logger

from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession
from keyboards import admit_decline_kb, schedule_kb
from services import GroupService, UserService



allowed_table = ['ИАИТ', 'ВБШ', "ИИЭГО", "ИНГТ", "ИТФ", "СПО", "СТФ", "ТЭФ", "ФАД", "ФММТ", "ФПГС", "ХТФ", "ЭТФ"]


        
class RegistartionUser(StatesGroup):
    waiting_for_faculty  = State()
    waiting_for_course = State()
    waiting_for_group = State()
    write_in_base = State()

#

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
            await message.answer("Все верно?", reply_markup = admit_decline_kb.as_markup(resize_keyboard=True))

            await state.set_state(RegistartionUser.write_in_base)

    except Exception:
        pass




allowed_table = ['ИАИТ', 'ВБШ', "ИИЭГО", "ИНГТ", "ИТФ", "СПО", "СТФ", "ТЭФ", "ФАД", "ФММТ", "ФПГС", "ХТФ", "ЭТФ"]
async def write_user_service(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        text = message.text
        user_service = UserService(session)
        group_service = GroupService(session)
        

        if text and text.upper() == "ДА":
            data = await state.get_data()  
            faculty = str(data.get('faculty', 0))
            course = int(data.get('course', 0))


            if faculty not in allowed_table:
                await message.answer("Факультет не найден, доступные:")
                await message.answer(str(allowed_table), reply_markup=ReplyKeyboardRemove())
                await message.answer("/start")
                await state.clear()


            group_name = (faculty + data.get('group', 0))

            group_id = await group_service.get_id(group_name, course)
        
            if group_id is None:
                await message.answer("Не найдена информация о группе, проверьте данные")
                return

            user = await user_service.add_user(message.chat.id, course, faculty, group_id, 'Not now')#type: ignore
            logger.info(f"logged succesfully with {course}\t{faculty}\t{group_id}")#-------------------------------------------------------------
            logger.info(f"logged succesfully with {user}")#--------------------------------------------------------------------------------------
            await message.answer("Можете пользоваться ботом", reply_markup=schedule_kb.as_markup(resize_keyboard=True))
            await state.clear()
            return


        logger.info("SOMEHOW RETURN DIDNT WORKED")#-----------------------------------------------------------
        await message.answer("Попробуйте еще раз, проверьте название группы", reply_markup=ReplyKeyboardRemove())
        await message.answer('/start')
        await state.clear()
        return

    except Exception as e:
        logger.exception('Problem with registration', e)
        await message.answer("Что-то пошло не так, попробуйте еще раз")
        await state.clear()
        return



   






