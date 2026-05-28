import requests            
import bs4                 
from DrissionPage import WebPage
import sqlite3             
import re                  
import json                


SITE_LINK = "https://samgtu.ru/students/schedule"
GET_GROUPS_LINK = "https://samgtu.ru/students/getgrouplist?Course={}&Faculty={}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}


#We use this to get all groups names and put it in the db
#Actually its a bad habit to write sql requests with f"{}"
#Sometimes ignore groups with other courser. i gues because groups has same id
def get_group_name_and_to_db(course, faculty_id):
    
    print("get group worked!\n\n\n")

    url = GET_GROUPS_LINK.format(course, faculty_id)
    print(url)
    
    resp = requests.get(url)
    html = resp.json()
        
    print(f"\n\n\n{html}\n\n\n")

    #its works because 'i' is a link to the object, not a copy
    for i in html:
        print(i)

        i['faculty_id'] = faculty_id
        i['Name'] = i['Name'].rsplit(None, 1)[-1]
        i['Name'] = i['Name'].replace("–", "")
        i['Name'] = i['Name'][2:]
        i['Name'] = i['Name'].upper()
        i["course"] = course
        del i['Sort']

    print(html)

#all_faculties()


faculty_id = 1
course = 1

while True:

    faculty_id = input("id факультета 0.Выход\n")
    faculty_id = int(faculty_id)

    if faculty_id == 0:

        break

        
    for i in range(1, 7):
        course = i
        get_group_name_and_to_db(course, faculty_id)

