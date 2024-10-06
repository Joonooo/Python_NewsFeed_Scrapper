import csv
import os
import re
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv


# 파일에 텍스트를 추가하는 함수
def append_to_file(file_path, text):
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(text + "\n")  # 파일 끝에 텍스트와 줄바꿈 추가

# 텍스트에 한글이 포함되어 있는지 확인하는 함수
def contains_korean(text):
    return bool(re.search('[\uAC00-\uD7AF]', text))  # 한글 유니코드 범위를 사용하여 검사


# 출력 파일 경로 설정
output_file_path = "tsv 파일 경로"

# 출력 파일 초기화
open(output_file_path, 'w').close()

# RSS 피드 데이터 가져오기
response = requests.get("http://api.newswire.co.kr/rss/all")
response.encoding = 'utf-8'  # 응답 인코딩 설정
xml_data = response.text  # 응답 텍스트 저장
root = ET.fromstring(xml_data)  # XML 데이터 파싱

# 파일에 헤더 쓰기
append_to_file(output_file_path, "title\tlink\tcategory\tdescription\tpubDate")

# 각 뉴스 아이템 처리
for item in root.findall("./channel/item"):
    # 각 필드 추출 및 필요시 작은따옴표 이스케이프 처리
    title = item.find("title").text.replace("'", "''").replace("\n", "|||")
    link = item.find("link").text.replace("'", "''").replace("\n", "|||")
    category = item.find("category").text.replace("'", "''").replace("\n", "|||")
    description = item.find("description").text.replace("\n", "|||")
    description = BeautifulSoup(description, "html.parser").get_text().replace("'", "''")
    pubDate = item.find("pubDate").text.replace("'", "''").replace("\n", "|||")
    
    # 제목에 한글이 포함되어 있으면 파일에 기록
    if contains_korean(title):
        append_to_file(output_file_path, f"{title}\t{link}\t{category}\t{description}\t{pubDate}")

# 데이터 읽기 및 저장
data = []
with open(output_file_path, newline='', encoding='utf-8') as file:
    reader = csv.reader(file, delimiter='\t')
    headers = next(reader)  # 헤더 읽기
    for row in reader:
        data.append(row)  # 나머지 데이터 저장

# SQL 명령 작성
sql_filename = 'sql 파일 경로'
with open(sql_filename, 'w', encoding='utf-8') as sql_file:
    for row in data:
        # INSERT 문 작성
        values = ', '.join([f"'{val}'" for val in row])
        command = f"INSERT INTO news (title, link, category, description, pubDate) VALUES ({values}) ON DUPLICATE KEY UPDATE title=VALUES(title), link=VALUES(link), category=VALUES(category), description=VALUES(description), pubDate=VALUES(pubDate);\n"
        sql_file.write(command)  # 파일에 SQL 명령 작성

# 환경 변수 로드
load_dotenv()
db_password = os.getenv('DB_PASSWORD')  # .env 파일에서 DB 비밀번호 가져오기

# 데이터베이스 정보
username = 'root'  # 사용자 이름
database = '데이터베이스 이름'  # 데이터베이스 이름

# MySQL 커맨드 구성
mysql_command = f"mariadb경로 -u{username} -p{db_password} {database} < {sql_filename}"

# os.system을 이용하여 커맨드 실행
status = os.system(mysql_command)
        
print("Done.")