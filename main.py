import vk_api
import json
import re
from pprint import pprint
from datetime import date, timedelta

from pymongo import MongoClient

client = MongoClient()
vkinder_db = client['VKinder_db']
subject_info_collection = vkinder_db['subj_info']
found_pid_collection = vkinder_db['found_pid']
output_data_collection = vkinder_db['output_data']


class Vkinder:

    def __init__(self, u_login, u_password):
        if not u_login:
            self.u_login = input('Ваш номер телефона Вконтакте: ')
        else:
            self.u_login = u_login

        if not u_password:
            self.u_password = input('Ваш пароль Вконтакте: ')
        else:
            self.u_password = u_password

        self.vk_session = vk_api.VkApi(self.u_login, self.u_password)
        self.vk_session.auth()
        self.vk = self.vk_session.get_api()
        self.user = self.vk.users.get()
        self.id = self.user[0]['id']

    def get_user_info(self, subject_id=None):
        if not subject_id:
            subject_id = self.id

        self.info_params = {
            'user_ids': subject_id,
            'fields': r"bdate, sex, city, country, " \
                      r"activities, interests, " \
                      r"music, movies, tv, books, games, screen_name"
        }

        self.subject_id_info = self.vk.users.get(user_ids=subject_id,
                                    fields=self.info_params['fields'])
        self.subject_id_int = self.subject_id_info[0]['id']
        self.subject_full_name = f"{self.subject_id_info[0]['first_name']} " \
                                 f"{self.subject_id_info[0]['last_name']}"

        if self.subject_id_info[0].get('bdate'):
            self.subject_bdate = self.subject_id_info[0][
                'bdate'].split('.')
        else:
            self.subject_bdate = input('Введите дату рождения '
                                       '(ДД.ММ.ГГГГ): ').split()

        # TODO: конвертировать дату рождения в datetime,
        #  получать из неё возраст (количество полных лет) и целевые
        #  возрастные рамки для поиска кандидатур

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
        else:
            self.subject_city = input('Ваш город проживания: ')

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

        self.sub_info_dict = {
            'id': self.subject_id_int,
            'name': self.subject_full_name,
            'birthdate': self.subject_bdate,  # заменить на birthdate
            'sex': self.subject_sex,
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

        return self.sub_info_dict

    def process_subject(self, subject_id=None,
                        db_name=vkinder_db.subject_info_collection):
        if subject_id == None:
            subject_id = self.id
        if db_name.find_one({'id': subject_id}):
            print('Субьект поиска уже в базе')
            return None
        self.subj_info = self.get_user_info(subject_id)
        self.subject_ins = db_name.insert_one(self.subj_info)
        return self.subject_ins.inserted_id

    def make_search_request(self, db_name=vkinder_db.subject_info_collection):

        # TODO: в рамках этого метода - захват большого количества данных
        #  c первоначальной выборкой (возраст, пол) и запись в коллекцию бд
        #  возможно с пометкой "кто искал"

        if db_name.find_one({'sex': 1}):
            self.target_sex = 2
        else:
            self.target_sex = 1
        self.search_req = self.vk.users.search(count=1000, fields = 'photo_id, '
                            'verified, sex, bdate, city, country, photo_max_orig, '
                            'has_mobile, relation, interests, music, movies, '
                            'books, games', sex=self.target_sex, status=6,
                            age_from=30, age_to=40, has_photo=1)
        return self.search_req

    def build_output(self):

        # TODO: В рамках этого метода - анализ данных, записанных в коллекцию
        #  в предыдущем. Сравниваем по нескольким показателям, делаем
        #  выборку, для верхних 10 значений - делаем словарь, куда находим
        #  залайканные 3 фотографии, и кидаем их в json

        self.search_res = self.make_search_request()
        self.output_list = []
        for item in self.search_res['items']:
            self.output_list.append(item)
        return self.output_list


if __name__ == '__main__':
    # Очистка БД - коллекция с инфой о пользователе
    # vkinder_db.subject_info_collection.drop()

    vk_phone = 'Vk phone login'
    vk_pass = 'Vk password'

    av = Vkinder(vk_phone, vk_pass)

    info = av.process_subject()
    pprint(info)
