import pandas, requests


def unpack_orders_xls(table, project_id, cookie):
    data_tuples = [tuple(x) for x in pandas.read_excel(table).values]

    for analytics_id, address, name, phone, price in data_tuples:
        if not (phone, name, address):
            return False
        if str(analytics_id) == 'nan':
            analytics_id = None
        if str(price) == 'nan':
            price = None

        response = requests.post('http://127.0.0.1:5000/api/orders',
                                 json={'phone': phone,
                                       'name': name,
                                       'address': address,
                                       'analytics_id': analytics_id,
                                       'price': price,
                                       'project_id': project_id}, cookies=cookie)
        if not response:
            return False
    return True
