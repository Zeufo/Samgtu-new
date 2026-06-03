import requests
import bs4
from DrissionPage import WebPage
import sqlite3
import re
import json

#TASKS:
#think about to connect all colleges in the one table, if groups 
#is not repeats

#main lin to the city where we taking info from
SITE_LINK = "https://samgtu.ru/students/schedule"

#This one we use to get all avaible groups in the faculty
#use int_name = link_name.format(course_id, faculty_id)
GET_GROUPS_LINK = "https://samgtu.ru/students/getgrouplist?Course={}&Faculty={}"


#GROUP_LINK = "https://samgtu.ru/students/getgrouplist?Course=1&Faculty=100108"


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}





#----------------------------------USE all_faculties TO CREATE DB WITH FACULTIES NAME----------------------------------



#we use this to get get data about faculties from cite 
def all_faculties():
    resp = requests.get(SITE_LINK)
    html = resp.text

    soup = bs4.BeautifulSoup(html, "lxml")
    obj = soup.find("select", class_="schedule-selects")

    if obj:
        obj = obj.find_all("option")
    
        faculties_id = []
        for i in obj:
            key = i.get("value")#Тут разворачиваем где value=""

            if key == "":
                continue

            faculties_id.append(key)




        print(f"\n\n{faculties_id}\n\n")
        
        #faculties_to_db(d)      
                










#We use this to get all groups names and put it in the db
#Actually its a bad habit to write sql requests with f"{}"
#this one we use to put info about faculties and them id 
#to the db.
def faculties_to_db(raw):
    try:

        raw = [[k, v] for k, v in raw.items()]

        val = "short"


        count = 0
        for i in raw:
            i.append(val + str(count))
            count = int(count) + 1


        raw.pop(0)


        print(f"raw is {raw}")

    except Exception as e:
        print(f"something went wrong... code is {e}")



faculty_id = 1
course = 1


def test():
    raw = requests.get('https://samgtu.ru/students/getgrouplist?Course=1&Faculty=113574')

    data = raw.json()
    print(data)



#test()
all_faculties()
#while faculty_id != 0:
#    course = 1
#    faculty_id = int(input("id факультета 0.Выход\n"))
#    faculty_name = input("название факультета\n")
#    
#    for i in range(1, 7):
#        course = i
#        get_group_name_and_to_db(course, faculty_id, faculty_name)
#

