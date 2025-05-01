import pandas as pd
import requests


def unpack_orders_xls(table):  # TODO: Доделать функцию, которая вытягивает данные с xls таблицы и кидает их в бд

    df = pd.read_excel(table)
    data_tuples = [tuple(x) for x in df.values]
    for analytics_id, address, name, phone, price in data_tuples:
        data = {
            'phone': phone,
            'name': name,
            'address': address,
            'analytics_id': analytics_id,
            'price': price
        }
        response = requests.post('http://127.0.0.1:5000/api/orders', json=json.dumps(data))
        if not response:
            raise Exception('REQUEST FAILED')
