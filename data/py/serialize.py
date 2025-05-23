from pandas import ExcelWriter, DataFrame, read_excel
from data.sql.db_session import create_session
from data.sql.models.order import Order
from flask import send_file
import requests, zipfile
from io import BytesIO


def unpack_orders_xls(table, project_id, cookie, host_url):
    # Читаем всю таблицу и проходимся по ней
    data_tuples = [tuple(x) for x in read_excel(table).values]
    for analytics_id, address, name, phone, comment, price in data_tuples:
        if not (phone, name, address):
            return False
        if str(analytics_id) == 'nan':
            analytics_id = None
        if str(price) == 'nan':
            price = None
        if str(comment) == 'nan':
            comment = None

        # Запрос на добавление заказов из таблицы
        response = requests.post(f'{host_url}api/orders',
                                 json={'phone': phone,
                                       'name': name,
                                       'address': address,
                                       'analytics_id': analytics_id,
                                       'price': price,
                                       'comment': comment,
                                       'project_id': project_id}, cookies=cookie)
        if response.status_code != 200:
            return False
    return True


def create_couriers_excel(project_id, couriers, one_file):
    """
    Создает Excel-файл(ы) с заказами курьеров в памяти и возвращает их как Flask-ответ.
    :param project_id: ID проекта
    :param couriers: список словарей вида {'id': 'courier_id', 'name': 'Courier Name'}
    :param one_file: если True — все курьеры в одном файле, иначе отдельные файлы в zip-архиве
    :return: Flask-ответ с файлом или архивом
    """
    with create_session() as session:
        if one_file:
            # Создаем один Excel-файл с несколькими листами
            output = BytesIO()
            with ExcelWriter(output, engine='xlsxwriter') as writer:
                for courier in couriers:
                    if isinstance(couriers, list):
                        courier_id = courier['id']
                        courier_name = courier['name']
                    elif isinstance(couriers, dict):
                        courier_id = courier
                        courier_name = couriers[courier_id]['name']

                    # Собираем данные о заказах
                    orders = []
                    for order in session.query(Order).filter(Order.project_id == project_id,
                                                             Order.who_delivers == courier_id).all():
                        orders.append({'Номер заказа': order.analytics_id if order.analytics_id else order.id,
                                       'Адрес': order.address,
                                       'Получатель': order.name,
                                       'Телефон': order.phone,
                                       'Цена': order.price,
                                       'Комментарий': order.comment})

                    if orders:
                        df = DataFrame(orders)
                        sheet_name = courier_name[:31]  # Ограничение Excel
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

            output.seek(0)
            return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             as_attachment=True, download_name=f'couriers_project_{project_id}.xlsx')
        else:
            # Создаем zip-архив с отдельными файлами для каждого курьера
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                for courier in couriers:
                    if isinstance(couriers, list):
                        courier_id = courier['id']
                        courier_name = courier['name']
                    elif isinstance(couriers, dict):
                        courier_id = courier
                        courier_name = couriers[courier_id]['name']

                    # Собираем данные о заказах
                    orders = []
                    for order in session.query(Order).filter(Order.project_id == project_id,
                                                             Order.who_delivers == courier_id).all():
                        orders.append({'Номер заказа': order.analytics_id if order.analytics_id else order.id,
                                       'Адрес': order.address,
                                       'Получатель': order.name,
                                       'Телефон': order.phone,
                                       'Цена': order.price,
                                       'Комментарий': order.comment})

                    if orders:
                        excel_buffer = BytesIO()
                        DataFrame(orders).to_excel(excel_buffer, index=False)
                        excel_buffer.seek(0)
                        zip_file.writestr(f'{courier_name}.xlsx', excel_buffer.getvalue())

            zip_buffer.seek(0)
            return send_file(zip_buffer, mimetype='application/zip', as_attachment=True,
                             download_name=f'couriers_project_{project_id}.zip')


def create_orders_excel(project_id):
    """
    Создает Excel-файл со всеми заказами проекта в памяти и возвращает как Flask-ответ.

    :param project_id: ID проекта
    :return: Flask-ответ с Excel-файлом
    """
    with create_session() as session:
        # Собираем данные о заказах
        orders_data = []
        for order in session.query(Order).filter(Order.project_id == project_id).all():
            order_info = {'Номер заказа': order.analytics_id if order.analytics_id else order.id,
                          'Адрес': order.address,
                          'Получатель': order.name,
                          'Телефон': order.phone,
                          'Цена': order.price,
                          'Комментарий': order.comment if hasattr(order, 'comment') else None, }
            orders_data.append(order_info)

        output = BytesIO()
        with ExcelWriter(output, engine='xlsxwriter') as writer:
            DataFrame(orders_data).to_excel(writer, index=False, sheet_name='Заказы')

        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=f'orders_project_{project_id}.xlsx')
