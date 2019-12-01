import re
from datetime import date
import pandas as pd


def string_to_list(regex, data_string, request: str):
    if not data_string:
        data_string = input(request)
    str_list = re.findall(regex, data_string,
                          flags=re.IGNORECASE)
    return str_list


def str_bdate_to_datetime(data_string, request: str):
    if not data_string:
        data_string = input(request)
    data = data_string.split('.')

    today = date.today()

    b_day = int(data[0])
    b_month = int(data[1])
    b_year = int(data[2])

    birthdate = date(day=b_day, month=b_month, year=b_year)

    age = (today.year - birthdate.year -
           ((today.month, today.day)
            < (birthdate.month, birthdate.day)))

    return birthdate, age


def read_vk_location(source_dict, data_string, request: str):
    if not data_string:
        loc_title = input(request)
        loc_id = None
        return loc_title, loc_id
    loc_title = (source_dict['country']['title'])
    loc_id = (source_dict['country']['id'])
    return loc_title, loc_id


def read_vk_person_sex(data_string, request: str):
    if not data_string:
        sex = input(request).lower()
        if 'м' in sex:
            sex = '2'
        else:
            sex = '1'
        return sex
    sex = data_string
    return sex


def build_subject_info(source_dict):
    """
    :param source_dict: json_данные, полученные по запросу vk_api
    :return:
    """

    subject_id_int = source_dict[0]['id']
    subj_full_name = f"{source_dict[0]['first_name']} " \
                     f"{source_dict[0]['last_name']}"

    subj_bdate, sub_age = (str_bdate_to_datetime
                           (source_dict[0].get('bdate'),
                            'Введите дату рождения (ДД.ММ.ГГГГ): '))

    subj_sex = read_vk_person_sex(source_dict[0].get('sex'),
                                  'Введите свой пол (М/Ж): ')

    subj_country, subj_country_id = read_vk_location(
        source_dict[0],
        source_dict[0].get('country'),
        'Ваша страна проживания: ')

    subj_city, subj_city_id = read_vk_location(
        source_dict[0],
        source_dict[0].get('city'),
        'Ваш город проживания: ')

    subj_i_regex = r'[«\"A-Za-zА-я0-9:\-»]+'

    subj_music = string_to_list(
        subj_i_regex, source_dict[0].get('music'),
        'Любимые музыканты? ')

    subj_movies = string_to_list(
        subj_i_regex, source_dict[0].get('movies'),
        'Любимые кинофильмы? ')

    subj_books = string_to_list(
        subj_i_regex, source_dict[0].get('books'),
        'Любимые книги? ')

    subj_games = string_to_list(
        subj_i_regex, source_dict[0].get('games'),
        'Любимые игры? ')

    subj_interests = string_to_list(
        subj_i_regex, source_dict[0].get('interests'),
        'Ваши интересы? ')

    subj_info_dict = {
        'id': subject_id_int,
        'name': subj_full_name,
        'birthdate': subj_bdate,  # self.subject_bdate
        'age': sub_age,
        'sex': subj_sex,
        'city_id': subj_city_id,
        'city': subj_city,
        'country_id': subj_country_id,
        'country': subj_country,
        # 'friends': self.subj_friends,
        # 'groups': self.subj_groups,
        'music': subj_music,
        'movies': subj_movies,
        'books': subj_books,
        'games': subj_games,
        'interests': subj_interests
    }

    return subj_info_dict


def target_vk_sex(source_sex):
    if source_sex == 2:
        target_sex = 1
    else:
        target_sex = 2
    return target_sex


def target_vk_age(source_age):
    target_age = [source_age - 2, source_age + 2]
    return target_age


def get_rating_from_items(person, key: str, source_list):
    rating = 0
    if person.get(key):
        for item in source_list[key]:
            items_regex = f'{item}'
            matches = re.findall(
                items_regex, person[key], flags=re.I
            )
            rating += len(matches)
    return rating


def get_rating_from_lists(source, target):
    source_set = set(source)
    target_set = set(target)
    rating = len(set.intersection(source_set, target_set))
    return rating


def get_rating_from_location(person, key: str, source):
    rating = 0
    if person.get(key):
        if person[key]['title'] == source[key]:
            rating += 1
    return rating


def get_final_rating(friends, interests, city,
                     movies, music, groups,
                     books, games):
    final_rating = ((friends * 3) + (interests * 3)
                    + (city * 2) + groups + books
                    + (movies * 2) + (music * 2) + games)
    return final_rating


def build_json(source_list, photo_request: dict):
    output_dict = {}
    dict_to_json = {}

    for user_id in source_list:
        photo_dict = {}
        output_dict[f'{user_id}'] = []
        for item in photo_request:
            photo_dict = {
                'url': item['sizes'][-1]['url'],
                'likes': item['likes']['count']
            }
            output_dict[f'{user_id}'].append(photo_dict)

    for person in output_dict:
        dict_to_json.setdefault(person, {})
        dict_to_json[person]['profile_link'] = (r'https://vk.com/id'
                                                + str(person))
        ph_d = pd.DataFrame.from_records(output_dict[person])
        person_photos = (ph_d.sort_values('likes', ascending=False)
                         .head(3).to_dict('r'))
        for count, item in enumerate(person_photos):
            dict_to_json[person][
                'Photo0{}'.format(count + 1)] = item['url']
    return dict_to_json


if __name__ == '__main__':
    pass
