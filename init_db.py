import requests
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient           # pymongo를 임포트 하기(패키지 인스톨 먼저 해야겠죠?)
import random

client = MongoClient('localhost', 27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbjungle                      # 'dbjungle'라는 이름의 db를 만듭니다


def insert_all():
    # 타겟 URL을 읽어서 HTML를 받아오고,
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get('https://search.daum.net/search?w=tot&DA=TMZ&q=%EC%9D%BC%EA%B0%84%EC%98%81%ED%99%94%EC%88%9C%EC%9C%84', headers=headers)

    # HTML을 BeautifulSoup이라는 라이브러리를 활용해 검색하기 용이한 상태로 만듦
    # soup이라는 변수에 "파싱 용이해진 html"이 담긴 상태가 됨
    # 이제 코딩을 통해 필요한 부분을 추출하면 된다.
    soup = BeautifulSoup(data.text, 'html.parser')
    #print(soup)  # HTML을 받아온 것을 확인할 수 있다.


    movies = soup.select('#morColl > div.coll_cont > div > ol > li')

    for movie in movies :
        movie_info = movie.select_one('div.wrap_cont')
        
        movie_thumb = movie.select_one('div.wrap_thumb > a > img.thumb_img')['data-original-src']
        print(movie_thumb)
        if not movie_info :
            continue
        #print(movie_info)
        movie_info = movie_info.text.split("   ")
        temp=[] #임시로 사용하기 위한 리스트
        del movie_info[0]
        
        for i in movie_info :
            i = i.strip()
            temp.append(i)
            if '평점' in temp:
                temp.remove('평점')
        movie_info.clear()
        for info in temp :
            info = info.replace('개봉', '').replace('재','').replace('누적', '').replace('명','').replace(',', '').strip()
            movie_info.append(info)
        movie_info[0] = temp[0] #제목원본 보존
        print(movie_thumb)
        open_year, open_month, open_day = None, None, None
        for date in movie_info :
            if re.match(r'\d{4}\.\d{2}', date) :
                if date.count('.') == 3:
                    date_elements = date.split('.')
                    (open_year, open_month, open_day) = int(date_elements[0]), int(date_elements[1]), int(date_elements[2])
                    
                else :
                    (open_year, open_month) = date.split('.')
                    (open_year, open_month) = int(date_elements[0]), int(date_elements[1])
            
        viewers = None
        for person in movie_info:
            if person.isdigit():
                person = person.replace(',', '').strip()
                person = int(person)
                viewers = person
        movie_info_url = 'https://search.daum.net/search'
        movie_info_url += movie.select_one(' div.wrap_cont > div > a')['href']

        likes = random.randrange(0, 100)
        
        doc = {
            'title' : movie_info[0],
            'open_year' : open_year,
            'open_month' : open_month,
            'open_day' : open_day,
            'viewers' : viewers,
            'poster_url' : movie_thumb,
            'info_url' : movie_info_url,
            'likes' : likes,
            'trashed' : False
        }
        db.movies.insert_one(doc)
        print('완료 : ', movie_info[0], open_year, open_month, open_day, viewers)

if __name__ == '__main__' :
    db.movies.drop()
    insert_all()
            
            
    
