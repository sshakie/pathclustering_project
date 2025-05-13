from math import radians, sin, cos, atan2, sqrt
from data.sql.models.order import Order
import networkx as nx
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform


class Depot:
    """Класс склада, используется как специальный заказ с координатами."""
    def __init__(self, id, coords):
        self.id = id
        self.coords = coords

    def get_coords(self):
        return self.coords


def cluster_orders(orders, edges, num_couriers, depot):
    """Кластеризация заказов на основе расстояний между ними."""
    G = nx.Graph()
    G.add_weighted_edges_from(edges)  # Добавляем рёбра с весами (расстояниями)
    nodes = [node for node in orders if node != depot]

    # Получаем матрицу кратчайших путей между всеми вершинами графа
    dist_matrix = nx.floyd_warshall_numpy(G, weight='weight')

    # Определяем индексы только нужных узлов (заказов без склада)
    idx = [list(G.nodes).index(n) for n in nodes]

    # Строим подматрицу расстояний только между заказами
    reduced_matrix = dist_matrix[np.ix_(idx, idx)]

    # Преобразуем квадратную матрицу расстояний в сжатый (condensed) формат
    condensed = squareform(reduced_matrix)

    # Иерархическая кластеризация (метод: среднее расстояние)
    z = linkage(condensed, method='average')

    # Формируем кластеры с ограничением на число курьеров
    labels = fcluster(z, t=num_couriers, criterion='maxclust')

    # Распределяем заказы по кластерам
    clusters = {}
    for node, label in zip(nodes, labels):
        clusters.setdefault(label, []).append(node)

    return clusters


def haversine(coord1, coord2):
    """Вычисляет расстояние между двумя точками"""
    R = 6371000  # Радиус Земли в метрах

    # Преобразуем координаты в радианы
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Формула гаверсинуса
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c  # Возвращаем расстояние в метрах


def get_distance_matrix(orders: list[Order]) -> list[tuple[str, str, float]]:
    """Создаёт список расстояний между всеми парами заказов."""
    coords = [order.get_coords() for order in orders]
    ids = [order.id for order in orders]

    result = []

    # Вычисляем попарные расстояния (симметричная матрица, храним только верхнюю часть)
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            distance_meters = haversine(coords[i], coords[j])
            result.append((ids[i], ids[j], distance_meters))

    return result  # Список кортежей (id1, id2, расстояние)


def clustering(orders_list: list[Order], num_couriers: int, depot_coords: list):
    """
    Главная функция кластеризации.
    :param orders_list: список заказов
    :param num_couriers: количество курьеров (кластеров)
    :param depot_coords: координаты склада (точки начала маршрутов)
    """
    # Добавляем "фиктивный заказ" — склад с уникальным id = -1
    orders_list.append(Depot(id=-1, coords=depot_coords))

    # Формируем список расстояний между всеми точками
    matrix = get_distance_matrix(orders_list)

    # Получаем id всех точек (включая склад)
    ids = [order.id for order in orders_list]

    # Выполняем кластеризацию заказов
    return cluster_orders(ids, matrix, num_couriers, -1)
