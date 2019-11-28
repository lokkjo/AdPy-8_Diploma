import re
import vk_api
import json
from pprint import pprint
from datetime import date
import random
import time
import pandas as pd
from pymongo import MongoClient

from Vkinder_service import JSONEncoder, captcha_handler

client = MongoClient()
vkinder_db = client['VKinder_db']
output_data_collection = vkinder_db['output_data']



class Vkinder:
    def __init__(self, u_login, u_password):
        if not u_login:
            self.u_login = input('Ваш номер телефона Вконтакте: ')
        self.u_login = u_login

        if not u_password:
            self.u_password = input('Ваш пароль Вконтакте: ')
        self.u_password = u_password

        self.vk_session = vk_api.VkApi(self.u_login, self.u_password,
                                       scope='friend, photo, offline, groups',
                                       api_version='5.103', app_id=7219768,
                                       captcha_handler=captcha_handler)

        self.vk_session.auth()

        self.vk = self.vk_session.get_api()
        self.user = self.vk.users.get()
        self.id = self.user[0]['id']
        self.vk_tools = vk_api.VkTools(self.vk_session)
        print(f'\nПривет, {self.user[0]["first_name"]}')

    def get_subject_info(self, subject_id=None):
        if not subject_id:
            subject_id = self.id

        self.info_fields = """bdate, sex, city, country, activities, 
        interests, music, movies, tv, books, games, screen_name"""

        self.subject_id_info = self.vk.users.get(user_ids=subject_id,
                                                 fields=
                                                 self.info_fields)

        self.subject_id_int = self.subject_id_info[0]['id']
        self.subject_full_name = f"{self.subject_id_info[0]['first_name']} " \
                                 f"{self.subject_id_info[0]['last_name']}"

        if self.subject_id_info[0].get('bdate'):
            self.subject_bdate = self.subject_id_info[0][
                'bdate'].split('.')
        else:
            self.subject_bdate = input('Введите дату рождения '
                                       '(ДД.ММ.ГГГГ): ').split('.')

        self.sub_b_day = int(self.subject_bdate[0])
        self.sub_b_month = int(self.subject_bdate[1])
        self.sub_b_year = int(self.subject_bdate[2])
        self.sub_birthdate = date(self.sub_b_year, self.sub_b_month,
                                  self.sub_b_day)

        self.today = date.today()
        self.sub_age = (self.today.year - self.sub_birthdate.year -
                        ((self.today.month, self.today.day) <
                         (self.sub_birthdate.month,
                          self.sub_birthdate.day)))

        if self.subject_id_info[0].get('sex'):
            self.subject_sex = self.subject_id_info[0]['sex']
        else:
            self.subject_sex = input(
                'Введите свой пол (М/Ж): ').lower()
            if 'м' in self.subject_sex:
                self.subject_sex = '2'
            else:
                self.subject_sex = '1'

        if self.subject_id_info[0].get('country'):
            self.subject_country = \
                self.subject_id_info[0]['country']['title']
        else:
            self.subject_country = input('Ваша страна проживания: ')

        if self.subject_id_info[0].get('city'):
            self.subject_city = self.subject_id_info[0]['city'][
                'title']
            self.subject_city_id = self.subject_id_info[0]['city'][
                'id']
        else:
            self.subject_city = input('Ваш город проживания: ')
            self.subject_city = None

        if self.subject_id_info[0].get('music'):
            self.subject_music = self.subject_id_info[0][
                'music'].split(', ')
        else:
            self.subject_music = input('Три любимых музыкальных '
                                       'исполнителя? ').split()

        if self.subject_id_info[0].get('movies'):
            self.subject_movies = self.subject_id_info[0][
                'movies'].split(', ')
        else:
            self.subject_movies = input('Три ваши любимые '
                                        'киноленты: ').split()

        if self.subject_id_info[0].get('books'):
            self.subject_books = self.subject_id_info[0][
                'books'].split(', ')
        else:
            self.subject_books = input('Три любимые книги: ').split()

        if self.subject_id_info[0].get('games'):
            self.subject_games = self.subject_id_info[0][
                'games'].split(', ')
        else:
            self.subject_games = input('Три любимых игры: ').split()

        if self.subject_id_info[0].get('interests'):
            self.subject_interests = self.subject_id_info[0][
                'interests'].split(', ')
        else:
            self.subject_interests = input(
                'Укажите ваши хобби').split()

        self.subject_friends_info = self.vk.friends.get(
            user_id=self.subject_id_int)
        self.subject_friends = self.subject_friends_info['items']

        self.subject_groups_info = self.vk.groups.get(
            user_id=self.subject_id_int)
        self.subject_groups = self.subject_groups_info['items']

        self.subj_info_dict = {
            'id': self.subject_id_int,
            'name': self.subject_full_name,
            'birthdate': self.sub_birthdate,  # self.subject_bdate
            'age': self.sub_age,
            'sex': self.subject_sex,
            'city_id': self.subject_city_id,
            'city': self.subject_city,
            'country': self.subject_country,
            'friends': self.subject_friends,
            'groups': self.subject_groups,
            'music': self.subject_music,
            'movies': self.subject_movies,
            'books': self.subject_books,
            'games': self.subject_games,
            'interests': self.subject_interests
        }

        print('subj_info_dict')
        print(self.subj_info_dict)
        print('\n')

        return self.subj_info_dict

    def make_search_request(self, subject_id=None):

        # TODO: в рамках этого метода - захват большого количества данных
        #  c первоначальной выборкой (возраст, пол) и запись в коллекцию бд
        #  возможно с пометкой "кто искал"

        if subject_id == None:
            subject_id = self.id
        self.subj_info_dict = self.get_subject_info(subject_id)
        if self.subj_info_dict['sex'] == 1:
            self.target_sex = 2
        else:
            self.target_sex = 1
        self.target_age = [self.subj_info_dict['age'] - 2,
                           self.subj_info_dict['age'] + 2]
        self.search_fields = "photo_id, verified, sex, bdate, city, " \
                             "country, photo_max_orig, has_mobile, " \
                             "relation, interests, music, movies, " \
                             "books, games"
        time.sleep(0.5)
        if self.subj_info_dict['city_id']:
            self.search_req = (self.vk.users.search
                               (count=100, fields=self.search_fields,
                                city=self.subj_info_dict['city_id'],
                                sex=self.target_sex, status=6,
                                offset=random.randint(0, 900),
                                age_from=self.target_age[0],
                                age_to=self.target_age[1],
                                has_photo=1, online=1))
        else:
            self.search_req = (self.vk.users.search
                               (count=100, fields=self.search_fields,
                                sex=self.target_sex, status=6,
                                offset=random.randint(0, 900),
                                age_from=self.target_age[0],
                                age_to=self.target_age[1],
                                has_photo=1, online=1))

        return self.search_req

    def search_request_processing(self, subject_id=None):
        if subject_id == None:
            subject_id = self.id

        self.search_req = self.make_search_request(subject_id)
        self.tuples_list = []

        for person in self.search_req['items']:
            print(f'\rОбработка информации: '
                  f'{self.search_req["items"].index(person) + 1} '
                  f'контакт из {len(self.search_req["items"])}',
                  end="", flush=True)
            try:
                if person.get('books'):
                    for item in self.subj_info_dict['books']:
                        self.books_regex = f'{item}'
                        self.books_matches = re.findall(
                            self.books_regex, person['books'],
                            flags=re.I)
                        self.books_rating = len(self.books_matches)
                else:
                    self.books_rating = 0
                if person.get('movies'):
                    for item in self.subj_info_dict['movies']:
                        self.movies_regex = f'{item}'
                        self.movies_matches = re.findall(
                            self.movies_regex, person['movies'],
                            flags=re.I)
                        self.movies_rating = len(self.movies_matches)
                else:
                    self.movies_rating = 0
                if person.get('music'):
                    for item in self.subj_info_dict['music']:
                        self.music_regex = f'{item}'
                        self.music_matches = re.findall(
                            self.music_regex, person['music'],
                            flags=re.I)
                        self.music_rating = len(self.music_matches)
                else:
                    self.music_rating = 0
                if person.get('games'):
                    for item in self.subj_info_dict['games']:
                        self.games_regex = f'{item}'
                        self.games_matches = re.findall(
                            self.games_regex, person['games'],
                            flags=re.I)
                        self.games_rating = len(self.games_matches)
                else:
                    self.games_rating = 0
                if person.get('interests'):
                    for item in self.subj_info_dict['interests']:
                        self.interests_regex = f'{item}'
                        self.interests_matches = re.findall(
                            self.interests_regex,
                            person['interests'], flags=re.I)
                        self.interests_rating = len(
                            self.interests_matches)
                else:
                    self.interests_rating = 0
                if person.get('city'):
                    if person['city']['title'] == \
                        self.subj_info_dict['city']:
                        self.city_rating = 1
                else:
                    self.city_rating = 0

                self.person_friends = set(self.vk.friends.get(
                    user_id=person['id']))
                self.target_friends = set(
                    self.subj_info_dict['friends'])
                self.friends_rating = len(set.intersection(
                    self.person_friends, self.target_friends))

                self.person_groups = set(self.vk.groups.get(
                    user_id=person['id']))
                self.target_groups = set(
                    self.subj_info_dict['groups'])
                self.groups_rating = len(set.intersection(
                    self.person_groups, self.target_groups))

                self.formula = ((self.friends_rating * 3)
                                + (self.interests_rating * 3)
                                + (self.city_rating * 2)
                                + self.groups_rating
                                + self.books_rating
                                + (self.movies_rating * 2)
                                + (self.music_rating * 2)
                                + self.games_rating)

                self.tuples_list.append((person['id'], self.formula))

            except vk_api.exceptions.ApiError:
                pass

        self.t_df = pd.DataFrame(self.tuples_list,
                                 columns=['id', 'score'])
        self.res_list = (self.t_df.sort_values
                         ('score', ascending=False)
                         .head(10)['id'].tolist())

        return self.res_list

    def json_output(self, subject_id=None):

        # TODO: В рамках этого метода - анализ данных, записанных в коллекцию
        #  в предыдущем. Сравниваем по нескольким показателям, делаем
        #  выборку, для верхних 10 значений - делаем словарь, куда находим
        #  залайканные 3 фотографии, и кидаем их в json

        if subject_id == None:
            subject_id = self.id
        self.output_list = self.search_request_processing(subject_id)
        self.output_dict = {}
        self.dict_to_json = {}
        for user_id in self.output_list:
            self.photo_dict = {}
            time.sleep(0.5)
            self.photo_req = self.vk.photos.get(owner_id=user_id,
                                                album_id='profile',
                                                rev=1, extended=1,
                                                photo_sizes=0)
            self.output_dict[f'{user_id}'] = []
            for item in self.photo_req['items']:
                self.photo_dict = {
                    'url': item['sizes'][-1]['url'],
                    'likes': item['likes']['count']
                }
                self.output_dict[f'{user_id}'].append(
                    self.photo_dict)
        for person in self.output_dict:
            self.dict_to_json.setdefault(person, {})
            self.dict_to_json[person][
                'profile_link'] = r'https://vk.com/id' + str(person)
            self.ph_d = pd.DataFrame.from_records(
                self.output_dict[person])
            self.person_photos = (self.ph_d.sort_values
                                  ('likes', ascending=False)
                                  .head(3).to_dict('r'))
            for count, item in enumerate(self.person_photos):
                self.dict_to_json[person][
                    'Photo0{}'.format(count + 1)] = item['url']
        JSONEncoder().encode(self.dict_to_json)

        print('dict_to_json')
        print(self.dict_to_json)
        print('\n')

        return self.dict_to_json

    def find_a_match(self, subject_id=None, json_dict=None,
                     file_name=None, db_name=None, to_file=True):
        if not subject_id:
            subject_id = self.id
        if not json_dict:
            json_dict = self.json_output()
        if not file_name:
            file_name = f'Vkinder_output_{subject_id}.json'
        if not db_name:
            db_name = vkinder_db.output_data_collection

        self.dict_to_json = self.json_output(subject_id)

        if to_file is True:
            with open(file_name, 'w',
                      encoding='utf8') as vkinder_json:
                data = json_dict
                json.dump(data, vkinder_json, ensure_ascii=False,
                          indent=2)
            print('\nFile output is finished')

        self.json_output_ins = db_name.insert_one(json_dict)
        print('\nDB output is finished')
        return self.json_output_ins.inserted_id


if __name__ == '__main__':
    # Очистка БД - коллекция с инфой о пользователе
    # vkinder_db.output_data_collection.drop()

    vk_phone = 'Vk phone login'
    vk_pass = 'Vk password'

    av = Vkinder(vk_phone, vk_pass)
    info = av.find_a_match()
    pprint(info)