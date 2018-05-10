import argparse
import urllib.request
import re
import collections
import pymorphy2
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


def parse_arguments():
    parser = argparse.ArgumentParser(description='Habr posts words rating')
    parser.add_argument('-p', '--pages', type=int, choices=range(1, 101),
                        metavar="[1-100]", help='enter the number of pages to be parsed', required=True)
    args = parser.parse_args()
    return args.pages - 1
    

def connect_to_habr(url):
    response = urllib.request.urlopen(url)
    return response.read()


def get_next_page(url):
    soup = BeautifulSoup(url, 'html.parser')
    next_page = soup.find(
        'a', class_='arrows-pagination__item-link arrows-pagination__item-link_next').get('href')
    return next_page


def get_all_pages(base_url):
    url = base_url + '/all'
    all_pages = []
    all_pages.append(url)
    for _ in range(parse_arguments()):
        all_pages.append(base_url + get_next_page(connect_to_habr(url)))
        url = base_url + get_next_page(connect_to_habr(url))
    return all_pages


def transform_date(date):
    get_date = date.split()
    months = dict(января=1, февраля=2, марта=3, апреля=4, мая=5, июня=6, июля=7, августа=8, сентября=9, октября=10, ноября=11, декабря=12)
    if get_date[0] == 'сегодня':
        post_date = datetime.today().strftime('%d/%m/%Y')
    elif get_date[0] == 'вчера':
        post_date = (datetime.today() - timedelta(days=1)).strftime('%d/%m/%Y')
    else:
        post_date = datetime(2018, int(months[get_date[1]]), int(get_date[0])).strftime('%d/%m/%Y')
    return post_date


def get_start_of_week(day):
    get_day = datetime.strptime(day, '%d/%m/%Y')
    start = get_day - timedelta(days=get_day.weekday())
    end = start + timedelta(days=6)
    return (start.strftime('%d/%m/%Y'), end.strftime('%d/%m/%Y'))


def get_data_from_page(url):
    articles_info = []
    soup = BeautifulSoup(url, 'html.parser')
    for article_block in soup.find_all('article', class_='post post_preview'):
        title_link = article_block.find('a', {'class': 'post__title_link'})
        title_date = article_block.find('span', {'class': 'post__time'})
        articles_info.append(
            {'title': title_link.text, 'date': get_start_of_week(transform_date(title_date.text))})
    return articles_info


def get_all_words_from_days(all_posts):
    words_on_days = {}
    lower_letters_regex = re.compile('[^а-я]')
    for i in range(len(all_posts)):
        if words_on_days.get(all_posts[i]['date']) == None:
            words_on_days.update({all_posts[i]['date']: lower_letters_regex.sub(
                ' ', (all_posts[i]['title']).lower().strip()).split()})
        else:
            words_on_days[all_posts[i]['date']] = words_on_days.get(all_posts[i]['date']) + lower_letters_regex.sub(
                ' ', (all_posts[i]['title']).lower().strip()).split()
    return words_on_days
        
def normalize_word(word):
    morph = pymorphy2.MorphAnalyzer()
    p = morph.parse(word)
    i = 0
    try:
        while p[i].tag.POS != 'NOUN':
            i += 1
        return p[i].normal_form
    except: 
        Exception


def update_words_for_normal_form(list_words):
    temp_list = []
    for word in range(len(list_words)):
        temp_list.append(normalize_word(list_words[word]))
    return temp_list


def output_word_stat(word_stat, top_size=3):
    words = []
    for word in word_stat[:top_size]:
        words.append(word)
    return words

def post_results():
    pass


if __name__ == '__main__':

    all_pages = get_all_pages('https://habr.com')
    all_posts = []
    
    for page in range(len(all_pages)):
        all_posts += get_data_from_page(connect_to_habr(all_pages[page]))

    statistic = get_all_words_from_days(all_posts)
    
    for key, value in statistic.items():
        temp_list = []
        for i in range(len(value)):
            if len(value[i]) > 3:
                normal_word = normalize_word(value[i])
                if normal_word != None:
                    temp_list.append(normal_word)
        statistic[key] = temp_list
        date = key
        words = output_word_stat(collections.Counter(temp_list).most_common())

        print('--------------------------------------')
        print('В период с ', date[0]
        , ' по ', date[1])
        print('Были популярны следующие 3 слова:')
        print(words[0][0],words[1][0],words[2][0])
