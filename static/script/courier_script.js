// === Глобальные переменные ===
let activeOrderId = null;

// === Функции для работы с картой ===
function addWarehouseToMap(map, coords) {
    const warehousePlacemark = new ymaps.Placemark(
        coords,
        {
            hintContent: 'Склад',
            balloonContent: 'Склад. Отсюда будут забирать заказы.'
        },
        {
            preset: 'islands#blackDeliveryCircleIcon',
            iconColor: '#000000'
        }
    );
    map.geoObjects.add(warehousePlacemark);
    return warehousePlacemark;
}

function searchAddress(map, address) {
    if (!address.trim()) return;

    ymaps.geocode(address).then(result => {
        const firstGeoObject = result.geoObjects.get(0);
        if (firstGeoObject) {
            const coords = firstGeoObject.geometry.getCoordinates();
            const name = firstGeoObject.getAddressLine();
            map.setCenter(coords, 16);
            map.balloon.open(coords, name, { closeButton: true });
        } else {
            alert("Адрес не найден.");
        }
    });
}

// === Функции для работы с заказами ===
function createOrderItem(order) {
    const orderNumber = order.analytics_id ? order.analytics_id : order.id;
    const item = document.createElement('div');
    item.className = 'order-item';
    item.dataset.id = order.id;

    item.innerHTML = `
        <div class="order-header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: bold;">№ ${orderNumber}</div>
            </div>
            <div class="order-address">${order.address}</div>
        </div>
        <div class="order-details hidden">
            <div><b>Имя:</b> ${order.name || '—'}</div>
            <div><b>Телефон:</b> ${order.phone || '—'}</div>
            <div><b>Комментарий:</b> ${order.comment || '—'}</div>
        </div>
        <div class="order-price" style="color: orangered; font-weight: 700; text-align: right;">${order.price} руб.</div>
    `;

    return item;
}

function createOrderMarker(map, order) {
    const mark = new ymaps.Placemark(order.coords, {
        balloonContent: order.address,
        hintContent: order.address
    }, {
        preset: 'islands#circleIcon',
        iconColor: '#4dd2ff',
        balloonAutoPan: false,
        hideIconOnBalloonOpen: false
    });

    map.geoObjects.add(mark);
    return mark;
}

function highlightOrder(id) {
    document.querySelectorAll('.order-item').forEach(el => {
        el.classList.toggle('active', el.dataset.id == id);
    });
}

// === Обработчики событий для заказов ===
function setupOrderClickHandler(item, order, mark, map) {
    item.addEventListener('click', (e) => {
        // Закрываем предыдущие открытые детали
        document.querySelectorAll('.order-details:not(.hidden)').forEach(details => {
            if (!details.closest('.order-item').isSameNode(item)) {
                details.classList.add('hidden');
            }
        });

        const details = item.querySelector('.order-details');
        const wasHidden = details.classList.contains('hidden');
        details.classList.toggle('hidden');

        if (wasHidden) {
            activeOrderId = order.id;
            highlightOrder(order.id);
            map.setCenter(order.coords);
            mark.balloon.open();
        } else {
            activeOrderId = null;
            highlightOrder(null);
            mark.balloon.close();
        }
    });
}

function setupMarkerClickHandler(mark, item) {
    mark.events.add('click', () => {
        item.click();
    });
}

// === Инициализация карты и заказов ===
function initializeOrders(map, orders) {
    const ordersList = document.getElementById('orders-list');
    const allPlacemarks = [];

    // Очищаем список перед добавлением новых заказов
    ordersList.innerHTML = '';

    // Обновляем счетчик заказов
    document.getElementById('orders-count').textContent = orders.length;

    // Инициализация заказов
    orders.forEach(order => {
        const item = createOrderItem(order);
        const mark = createOrderMarker(map, order);

        setupOrderClickHandler(item, order, mark, map);
        setupMarkerClickHandler(mark, item);

        allPlacemarks.push(mark);
        ordersList.appendChild(item);
    });
}

// === Инициализация карты Yandex ===
ymaps.ready(() => {
    const map = new ymaps.Map("map", {
        center: depotCoords,
        zoom: 14,
        controls: []
    });

    addWarehouseToMap(map, depotCoords);

    // Преобразуем courierOrders в плоский массив заказов
    const allOrders = Object.values(courierOrders).flat();
    initializeOrders(map, allOrders);

    // Поиск адресов
    const addressInput = document.getElementById('address-search');
    const addressBtn = document.getElementById('address-search-btn');

    addressBtn.addEventListener('click', () => searchAddress(map, addressInput.value));
    addressInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') searchAddress(map, addressInput.value);
    });

    // Поиск по заказам
    const orderSearch = document.getElementById('order-search');
    if (orderSearch) {
        orderSearch.addEventListener('input', () => {
            const query = orderSearch.value.toLowerCase();
            let visibleCount = 0;

            document.querySelectorAll('.order-item').forEach(order => {
                const orderText = order.textContent.toLowerCase();
                const isVisible = orderText.includes(query);
                order.style.display = isVisible ? 'block' : 'none';
                if (isVisible) visibleCount++;
            });

            // Обновляем счетчик видимых заказов
            document.getElementById('orders-count').textContent = visibleCount;
        });
    }
});