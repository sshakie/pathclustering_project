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


async def fetch_osrm_table(session: aiohttp.ClientSession, coords: list[tuple[float, float]]) -> dict:
    """Запрашивает матрицу расстояний из OSRM."""
    coordinates = ";".join([f"{lon},{lat}" for lon, lat in coords])
    url = f"http://router.project-osrm.org/table/v1/driving/{coordinates}?annotations=distance"

    async with session.get(url) as response:
        if response.status != 200:
            raise Exception(f"OSRM API error: {await response.text()}")
        return await response.json()


async def get_distance_matrix(orders: list[Order]) -> list[tuple[str, str, float]]:
    # Извлекаем координаты из заказов (OSRM ожидает lon, lat)
    coords = [order.get_coords() for order in orders]
    ids = [order.id for order in orders]

    async with aiohttp.ClientSession() as session:
        # Запрашиваем матрицу расстояний
        data = await fetch_osrm_table(session, coords)
        distances = data['distances']  # Матрица расстояний в метрах

        # Формируем список пар
        result = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):  # Чтобы избежать дубликатов (A-B и B-A)
                distance_meters = distances[i][j]
                result.append((ids[i], ids[j], distance_meters))

    return result


def clustering(orders_list: list[Order], num_couriers: int, depot_coords: list):
    ''':param orders_list Список заказов
        :param num_couriers Количество курьеров
        :param depot_coords Координаты начальной точки'''

    orders_list.append(Depot(id=-1, coords=depot_coords))
    matrix = asyncio.run(get_distance_matrix(orders_list))
    ids = [order.id for order in orders_list]
    return cluster_orders(ids, matrix, num_couriers, -1)

