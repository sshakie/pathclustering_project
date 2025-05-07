from math import radians, sin, cos, atan2, sqrt
import aiohttp
import asyncio
from data.sql.models.order import Order
import networkx as nx
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform


class Depot:
    def __init__(self, id, coords):
        self.id = id
        self.coords = coords

    def get_coords(self):
        return self.coords


def cluster_orders(orders, edges, num_couriers, depot):
    G = nx.Graph()
    G.add_weighted_edges_from(edges)

    nodes = [node for node in orders if node != depot]

    # Матрица кратчайших расстояний между заказами
    dist_matrix = nx.floyd_warshall_numpy(G, weight='weight')
    idx = [list(G.nodes).index(n) for n in nodes]
    reduced_matrix = dist_matrix[np.ix_(idx, idx)]

    # Кластеризация
    condensed = squareform(reduced_matrix)
    z = linkage(condensed, method='average')
    labels = fcluster(z, t=num_couriers, criterion='maxclust')

    # Сопоставляем точки с курьерами
    clusters = {}
    for node, label in zip(nodes, labels):
        clusters.setdefault(label, []).append(node)

    return clusters


def haversine(coord1, coord2):
    R = 6371000

    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def get_distance_matrix(orders: list[Order]) -> list[tuple[str, str, float]]:
    coords = [order.get_coords() for order in orders]
    ids = [order.id for order in orders]

    result = []
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            distance_meters = haversine(coords[i], coords[j])
            result.append((ids[i], ids[j], distance_meters))

    return result


def clustering(orders_list: list[Order], num_couriers: int, depot_coords: list):
    ''':param orders_list Список заказов
        :param num_couriers Количество курьеров
        :param depot_coords Координаты начальной точки'''

    orders_list.append(Depot(id=-1, coords=depot_coords))
    matrix = get_distance_matrix(orders_list)
    ids = [order.id for order in orders_list]
    print(matrix)
    return cluster_orders(ids, matrix, num_couriers, -1)

