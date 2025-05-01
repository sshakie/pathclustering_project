import pandas as pd
import requests


def unpack_orders_xls(table):  # TODO: Доделать функцию, которая вытягивает данные с xls таблицы и кидает их в бд

    df = pd.read_excel(table)
    data_tuples = [tuple(x) for x in df.values]

    for analytics_id, address, name, phone, price in data_tuples:
        if not (phone, name, address):
            return (False, 'Не хватает обязательных элементов')

        if str(analytics_id) == 'nan':
            analytics_id = None
        if str(price) == 'nan':
            price = None
        data = {
            'phone': phone,
            'name': name,
            'address': address,
            'analytics_id': analytics_id,
            'price': price,
            'apikey': '123',  # TODO: Переделать апи
        }
        print(data)
        response = requests.post('http://127.0.0.1:5000/api/orders', json=data)
        if not response:
            raise Exception('REQUEST FAILED', response.content)


if __name__ == '__main__':
    unpack_orders_xls('template.xlsx')
