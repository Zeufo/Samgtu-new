import asyncio
from aiogram.types import Message

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types


from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import User
from database.models import AsyncSessionLocal
allowed_table = ['ИАИТ', 'ВБШ', "ИИЭГО", "ИНГТ", "ИТФ", "СПО", "СТФ", "ТЭФ", "ФАД", "ФММТ", "ФПГС", "ХТФ", "ЭТФ"]


class UserService():
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_user(self, user_id: int, course: int, faculty: str, group_id: int, last_time_acive: str) -> User:
        new_user = User(user_id=user_id, course=course, faculty=faculty, group_id=group_id, last_time_acive=last_time_acive)
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        return new_user

                  




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




async def write_user_service(message: Message, state: FSMContext, conn, session: AsyncSession) -> None:
    try:
        text = message.text
            
        if text and text.upper() == "ДА":
            data = await state.get_data()  

            faculty = data.get('faculty') 

            if faculty not in allowed_table:

                await message.answer("Факультет не найден, доступные:")
                await message.answer(str(allowed_table), reply_markup=ReplyKeyboardRemove())
                await message.answer("/start")
                await state.clear()


            if faculty and data.get('group') is not None:
                group_name = (faculty + data.get('group_name'))

            else:
                await message.answer("Ошибка в названии группы, попробуйте еще раз", reply_markup=ReplyKeyboardRemove())
                await state.clear()
                return

#I dont think that we really need that check if user in the base. lets bettter solve it with upsert
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id FROM users WHERE user_id = ?", (message.chat.id,)) 
                user = await cur.fetchone() 

                await cur.execute(f"SELECT group_id FROM ({faculty}) WHERE group_name = ? AND course = ?", (group_name, data.get('course_name'),))
                row = await cur.fetchone()
                true_id = None

            if row:
                true_id = row[0]    


            if true_id is not None :
                if user is None:

                    to_insert = [message.chat.id, data.get("course_name"), data.get("faculty_name"), true_id]  
                    await cur.execute("INSERT INTO users (user_id, course, faculty, group_id) VALUES (?, ?, ?, ?)", to_insert)

                else:
                    await cur.execute("UPDATE users SET (user_id, course, faculty, group_id) = (?, ?, ?, ?) WHERE user_id = ?", (message.chat.id, data.get('course_name'), data.get('faculty_name'), true_id, message.chat.id,) )
                

                await cur.execute("INSERT OR IGNORE INTO all_groups(group_id) VALUES (?)", (true_id,))
                await db_conn.commit()
                await message.answer("Можете пользоваться ботом", reply_markup=base_kb.as_markup(resize_keyboard=True))
                await state.clear()
                return


            await message.answer("Попробуйте еще раз, проверьте название группы", reply_markup=ReplyKeyboardRemove())
            await message.answer('/start')

        await state.clear()
        return

    except Exception as e:
        print(f"Problem with write in db... {e}")
        await state.clear() 












    except Exception:
        pass
    
