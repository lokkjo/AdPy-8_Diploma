import vk_api
import json
import random
import pandas as pd
from pymongo import MongoClient
import Vkinder_inner as inner
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
                                       scope='friend, photo, '
                                             'offline, groups',
                                       api_version='5.103',
                                       app_id=7219768,
                                       captcha_handler=captcha_handler)

        self.vk_session.auth()

        self.vk = self.vk_session.get_api()
        self.user = self.vk.users.get()
        self.id = self.user[0]['id']
        self.vk_tools = vk_api.VkTools(self.vk_session)

        # Объявляем ключевые переменные для класса
        self.subj_info_dict = {}
        self.search_req = {}
        self.res_list = []
        self.dict_to_json = {}

        print(f'\nПривет, {self.user[0]["first_name"]}')

    def get_subject_info(self, subject_id=None):
        """
        :param subject_id: uid пользователя,
            по умолчанию - id залогиненного юзера
        :return:
        """
        if not subject_id:
            subject_id = self.id

        self.info_fields = """bdate, sex, city, country, activities, 
        interests, music, movies, books, games, screen_name"""

        self.subject_id_info = self.vk.users.get(user_ids=subject_id,
                                                 fields=
                                                 self.info_fields)

        self.subj_info_dict = inner.build_subject_info(
            source_dict=self.subject_id_info)

        self.subj_friends = (self.vk.friends.
                    get(user_id=self.subj_info_dict['id'])['items'])
        self.subj_info_dict['friends'] = self.subj_friends

        self.subj_groups = (self.vk.groups.
                    get(user_id=self.subj_info_dict['id'])['items'])
        self.subj_info_dict['groups'] = self.subj_groups

        return self.subj_info_dict

    def make_search_request(self, subject_id=None):

        if subject_id is None:
            subject_id = self.id

        self.get_subject_info(subject_id)

        self.target_sex = inner.target_vk_sex(self.subj_info_dict['sex'])

        self.target_age = inner.target_vk_age(self.subj_info_dict['age'])

        self.search_fields = "photo_id, verified, sex, bdate, city, " \
                             "country, photo_max_orig, has_mobile, " \
                             "relation, interests, music, movies, " \
                             "books, games"
        self.search_params = {
            'count': 1000,
            'fields': self.search_fields,
            'sex': self.target_sex,
            'status': 6,
            'offset': random.randint(0, 24000),
            'age_from': self.target_age[0],
            'age_to': self.target_age[1],
            'has_photo': 1,
            'online': 1
        }
        if self.subj_info_dict['city_id']:
            self.search_params['city'] = self.subj_info_dict['city_id']

        self.search_req = (self.vk_tools.get_all
                           ('users.search',max_count=1000,
                            values=self.search_params))

        return self.search_req

    def search_request_processing(self, subject_id=None):
        if subject_id == None:
            subject_id = self.id


        self.make_search_request(subject_id)
        self.tuples_list = []

        for person in self.search_req['items']:
            print(f'\rОбработка информации: '
                  f'{self.search_req["items"].index(person) + 1} '
                  f'контакт из {len(self.search_req["items"])}',
                  end="", flush=True)
            try:
                self.books_rating = inner.get_rating_from_items(
                    person, 'books', self.subj_info_dict
                )

                self.movies_rating = inner.get_rating_from_items(
                    person, 'movies', self.subj_info_dict
                )

                self.music_rating = inner.get_rating_from_items(
                    person, 'music', self.subj_info_dict
                )

                self.games_rating = inner.get_rating_from_items(
                    person, 'games', self.subj_info_dict
                )

                self.interests_rating = inner.get_rating_from_items(
                    person, 'interests', self.subj_info_dict
                )

                self.city_rating = inner.get_rating_from_location(
                    person, 'city', self.subj_info_dict
                )

                self.friends_rating = inner.get_rating_from_lists(
                    source=self.vk.friends.get(user_id=person['id']),
                    target=self.subj_info_dict['friends']
                )

                self.groups_rating = inner.get_rating_from_lists(
                    source=self.vk.groups.get(user_id=person['id']),
                    target=self.subj_info_dict['groups']
                )

                self.f_rating = inner.get_final_rating(
                    self.friends_rating, self.interests_rating,
                    self.city_rating, self.movies_rating,
                    self.music_rating, self.groups_rating,
                    self.books_rating, self.games_rating
                )

                self.tuples_list.append((person['id'], self.f_rating))

            except vk_api.exceptions.ApiError:
                pass

        self.t_df = pd.DataFrame(self.tuples_list,
                                 columns=['id', 'score'])
        self.res_list += (self.t_df.sort_values
                         ('score', ascending=False)
                         .head(10)['id'].tolist())

        return self.res_list

    def json_output(self, subject_id=None):
        if subject_id == None:
            subject_id = self.id

        self.search_request_processing(subject_id) # Бывшая 176

        for user_id in self.res_list:
            self.photo_req = self.vk.photos.get(owner_id=user_id,
                                                album_id='profile',
                                                rev=1, extended=1,
                                                photo_sizes=0)
        self.res_dict = inner.build_json(self.res_list,
                                             self.photo_req['items'])
        self.dict_to_json.update(self.res_dict)

        JSONEncoder().encode(self.dict_to_json)

        return self.dict_to_json

    def find_a_match(self, subject_id=None, json_dict=None,
                     file_name=None, db_name=None, to_file=True):
        if not subject_id:
            subject_id = self.id
        self.subject_id = subject_id

        self.json_output(self.subject_id)

        if not json_dict:
            json_dict = self.dict_to_json
        self.json_dict = json_dict
        if not file_name:
            file_name = f'Vkinder_output_{self.subject_id}.json'
        self.file_name = file_name
        if not db_name:
            db_name = vkinder_db.output_data_collection
        self.db_coll_name = db_name

        if to_file is True:
            with open(self.file_name, 'w',
                      encoding='utf8') as vkinder_json:
                data = self.json_dict
                json.dump(data, vkinder_json,
                          ensure_ascii=False, indent=2)
            print('\nFile output is finished')

        self.json_output_ins = self.db_coll_name.insert_one(self.json_dict)
        print('\nDB output is finished')

        return self.json_output_ins.inserted_id


if __name__ == '__main__':
    # Очистка БД - коллекция с инфой о пользователе
    # vkinder_db.output_data_collection.drop()

    vk_phone = 'Vk phone login'
    vk_pass = 'Vk password'

    av = Vkinder(vk_phone, vk_pass)
    av.find_a_match()

