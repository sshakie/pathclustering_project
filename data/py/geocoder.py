import requests


def get_coords_from_geocoder(toponym_to_find):
    with open('data/config', encoding='UTF-8') as file:  # API-ключ для геокодера
        api_key = file.read().split('\n')[1].split()[1]
        
    # Запрос к геокодеру
    response = requests.get('http://geocode-maps.yandex.ru/1.x/',
                            params={'apikey': api_key,
                                    'geocode': toponym_to_find,
                                    'format': 'json'})

    if not response:  # Обработка ошибочной ситуации
        pass

    # Получаем первый топоним из ответа геокодера
    toponym = response.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']

    # Долгота и широта
    toponym_longitude, toponym_lattitude = toponym['Point']['pos'].split(' ')
    self_point = f'{toponym_longitude},{toponym_lattitude}'
    return self_point
