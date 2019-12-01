import json
from bson import ObjectId



class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def captcha_handler(captcha):
    """
    from https://github.com/python273/vk_api/blob/master/examples/captcha_handle.py

    При возникновении капчи вызывается эта функция и ей передается
    объект капчи. Через метод get_url можно получить ссылку
    на изображение. Через метод try_again можно попытаться отправить
    запрос с кодом капчи
    """

    key = input(
        "Enter captcha code {0}: ".format(captcha.get_url())).strip()

    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key)
