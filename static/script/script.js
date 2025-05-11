// === Глобальные переменные и константы ===
const courierColors = ['#ff4d4d', '#4dd2ff', '#85e085', '#ffcc66', '#cc99ff', '#9966cc', '#ff9966'];
let clusteringSuccess = false;
let currentEditingOrder = null;

// === DOM элементы ===
const tabMap = document.getElementById("tab-map");
const tabCouriers = document.getElementById("tab-couriers");
const addressWrapper = document.getElementById("address-search-wrapper");
const mapWrapper = document.getElementById("map-wrapper");
const couriers = document.getElementById("couriers");
const exportbtn = document.getElementById("exportbtn");
const clusteringbtn = document.getElementById("clusteringbtn");

// === Вспомогательные функции ===
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
}

function highlightOrder(id) {
    document.querySelectorAll('.order-item').forEach(el => {
        el.classList.toggle('active', el.dataset.id == id);
    });
}

function copyInviteLink() {
    const input = document.getElementById('inviteLinkInput');
    input.select();
    document.execCommand('copy');

    const btn = document.querySelector('.invite-btn');
    btn.classList.add('copied');
    setTimeout(() => btn.classList.remove('copied'), 1000);
}

// Добавляем обработчик для кнопки копирования
document.querySelector('.invite-btn')?.addEventListener('click', copyInviteLink);

// === Управление вкладками ===
function activateTab(tab) {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
}

function switchToCouriersTab() {
    activateTab(tabCouriers);
    addressWrapper.classList.add("hidden");
    mapWrapper.classList.add("hidden");
    couriers.classList.remove("hidden");
    exportbtn.classList.add("hidden");
    clusteringbtn.classList.add("hidden");
    document.querySelectorAll('.import-btn, .imp-title').forEach(el => el.classList.add("hidden"));
}

tabMap.addEventListener("click", () => {
    activateTab(tabMap);
    addressWrapper.classList.remove("hidden");
    mapWrapper.classList.remove("hidden");
    couriers.classList.add("hidden");
    exportbtn.classList.remove("hidden");
    clusteringbtn.classList.remove("hidden");
    document.querySelector('.import-btn')?.classList.remove("hidden");
});

tabCouriers.addEventListener("click", switchToCouriersTab);

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
function createOrderItem(order, courierId, color) {
    const orderNumber = order.analytics_id ? order.analytics_id : order.id;
    const item = document.createElement('div');

    item.className = courierId === 'no_courier' ? 'order-item unassigned' : 'order-item';
    item.dataset.id = order.id;
    item.dataset.courier = courierId;

    item.innerHTML = `
        <div class="order-header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: bold;">№ ${orderNumber}</div>
                <div style="display: flex; align-items: center;">
                    <button class="delete-order-btn hidden" style="height: 24px; display: flex; align-items: center; justify-content: center; margin-right: 10px;">🗑️</button>
                    <button class="edit-btn" style="height: 24px; display: flex; align-items: center; justify-content: center;">✏️</button>
                </div>
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

// Новая функция для создания элемента нового заказа
function createNewOrderItem() {
    const item = document.createElement('div');
    item.className = 'order-item new-order';
    item.innerHTML = `
        <div class="order-header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: bold;">Новый заказ</div>
                <div style="display: flex; align-items: center;">
                    <button class="cancel-new-order-btn" style="height: 24px; display: flex; align-items: center; justify-content: center; margin-right: 5px;">✖</button>
                    <button class="save-new-order-btn" style="height: 24px; display: flex; align-items: center; justify-content: center;">✅</button>
                </div>
            </div>
            <div class="order-address"><input type="text" placeholder="Адрес" class="new-order-input" style="width: 100%;"></div>
        </div>
        <div class="order-details">
            <div><b>Имя:</b> <input type="text" placeholder="Имя" class="new-order-input" style="width: 70%;"></div>
            <div><b>Телефон:</b> <input type="text" placeholder="Телефон" class="new-order-input" style="width: 70%;"></div>
            <div><b>ID аналитики:</b> <input type="text" placeholder="Необязательно" class="new-order-input" style="width: 70%;"></div>
            <div><b>Комментарий:</b> <input type="text" placeholder="Комментарий" class="new-order-input" style="width: 70%;"></div>
        </div>
        <div class="order-price" style="display: flex; justify-content: flex-end; align-items: center;">
            <input type="number" placeholder="Цена" class="new-order-input" style="width: 30%; text-align: right;"> руб.
        </div>
    `;
    return item;
}

function createOrderMarker(map, order, courierId, color) {
    if (courierId === 'no_courier') {
        const mark = new ymaps.Placemark(order.coords, {
            balloonContent: order.address,
            hintContent: 'Не назначен'
        }, {
            preset: 'islands#circleIcon',
            iconColor: '#808080',
            balloonAutoPan: false,
            hideIconOnBalloonOpen: false
        });
        mark.properties.set('courierId', courierId);
        map.geoObjects.add(mark);
        return mark;
    }

    const glowSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80">
            <defs>
                <radialGradient id="grad" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stop-color="${color}" stop-opacity="0.6"/>
                    <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
                </radialGradient>
            </defs>
            <circle cx="40" cy="40" r="30" fill="url(#grad)"/>
            <circle cx="40" cy="40" r="8" fill="${color}"/>
        </svg>
    `;

    const encodedSvg = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(glowSvg);
    const mark = new ymaps.Placemark(order.coords, {
        balloonContent: order.address,
        hintContent: courierData[courierId]?.name || courierId
    }, {
        iconLayout: 'default#image',
        iconImageHref: encodedSvg,
        iconImageSize: [80, 80],
        iconImageOffset: [-40, -40],
        balloonAutoPan: false,
        hideIconOnBalloonOpen: false
    });

    mark.properties.set('courierId', courierId);
    map.geoObjects.add(mark);
    return mark;
}

// === Обработчики событий для заказов ===
function setupOrderClickHandler(item, order, mark, map) {
    item.addEventListener('click', (e) => {
        const editBtn = item.querySelector('.edit-btn');
        const deleteBtn = item.querySelector('.delete-order-btn');

        if (e.target === editBtn || e.target === deleteBtn || editBtn.textContent === '✅' || currentEditingOrder) {
            return;
        }

        document.querySelectorAll('.order-details:not(.hidden)').forEach(openDetails => {
            if (openDetails !== item.querySelector('.order-details')) {
                const parentItem = openDetails.closest('.order-item');
                if (parentItem) {
                    openDetails.classList.add('hidden');
                    parentItem.querySelector('.edit-btn').style.display = 'flex';
                    parentItem.querySelector('.delete-order-btn').classList.add('hidden');
                }
            }
        });

        const details = item.querySelector('.order-details');
        const wasHidden = details.classList.contains('hidden');
        details.classList.toggle('hidden');

        editBtn.style.display = 'flex';
        deleteBtn.classList.toggle('hidden', !wasHidden);

        if (wasHidden) {
            map.setCenter(order.coords);
            mark.balloon.open();
            highlightOrder(order.id);
        }
    });
}

function setupMarkerClickHandler(item, order, mark) {
    mark.events.add('click', () => {
        if (!currentEditingOrder) {
            item.click();
        }
    });
}

function setupEditButtonHandler(item, order, mark, map) {
    const editBtn = item.querySelector('.edit-btn');
    const deleteBtn = item.querySelector('.delete-order-btn');
    const details = item.querySelector('.order-details');
    const addressEl = item.querySelector('.order-address');
    const priceEl = item.querySelector('.order-price');

    editBtn.addEventListener('click', async (e) => {
        e.stopPropagation();

        const nameEl = details.querySelector('div:nth-child(1)');
        const phoneEl = details.querySelector('div:nth-child(2)');
        const commentEl = details.querySelector('div:nth-child(3)');

        if (editBtn.textContent === '✏️') {
            // Начало редактирования
            currentEditingOrder = order.id;
            editBtn.textContent = '✅';
            deleteBtn.classList.remove('hidden');
            details.classList.remove('hidden');

            // Сохраняем оригинальные значения
            const originalValues = {
                name: nameEl.textContent.replace('Имя:', '').trim(),
                phone: phoneEl.textContent.replace('Телефон:', '').trim(),
                comment: commentEl.textContent.replace('Комментарий:', '').trim(),
                price: priceEl.textContent.replace('руб.', '').trim(),
                address: addressEl.textContent.trim()
            };

            // Создаем поля ввода с сохранением стилей
            nameEl.innerHTML = `<b>Имя:</b> <input type="text" value="${originalValues.name}" style="border:none; border-bottom: 1px solid #aaa; outline:none; background:none; font-size:14px; width:70%;">`;
            phoneEl.innerHTML = `<b>Телефон:</b> <input type="text" value="${originalValues.phone}" style="border:none; border-bottom: 1px solid #aaa; outline:none; background:none; font-size:14px; width:70%;">`;
            commentEl.innerHTML = `<b>Комментарий:</b> <input type="text" value="${originalValues.comment}" style="border:none; border-bottom: 1px solid #aaa; outline:none; background:none; font-size:14px; width:70%;">`;
            priceEl.innerHTML = `<input type="number" value="${parseInt(originalValues.price)}" style="border:none; border-bottom: 1px solid #aaa; outline:none; background:none; font-weight:700; text-align:right; width:30%;"> руб.`;
            addressEl.innerHTML = `<input type="text" value="${originalValues.address}" style="border:none; border-bottom: 1px solid #aaa; outline:none; background:none; font-size:14px; width:100%;">`;

            // Сохраняем оригинальный адрес для сравнения
            addressEl.dataset.originalAddress = originalValues.address;
        } else {
            // Завершение редактирования
            const currentValues = {
                name: nameEl.querySelector('input').value,
                phone: phoneEl.querySelector('input').value,
                comment: commentEl.querySelector('input').value,
                price: priceEl.querySelector('input').value,
                address: addressEl.querySelector('input').value
            };

            try {
                const res = await fetch(`/api/orders/${order.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        name: currentValues.name,
                        phone: currentValues.phone,
                        comment: currentValues.comment,
                        price: parseInt(currentValues.price),
                        address: currentValues.address
                    }),
                });

                if (res.ok) {
                    // Обновляем интерфейс
                    nameEl.innerHTML = `<b>Имя:</b> ${currentValues.name || '—'}`;
                    phoneEl.innerHTML = `<b>Телефон:</b> ${currentValues.phone || '—'}`;
                    commentEl.innerHTML = `<b>Комментарий:</b> ${currentValues.comment || '—'}`;
                    priceEl.innerHTML = `${currentValues.price} руб.`;
                    addressEl.innerHTML = currentValues.address;

                    // Обновляем маркер на карте
                    mark.properties.set('balloonContent', currentValues.address);

                    // Выходим из режима редактирования
                    editBtn.textContent = '✏️';
                    deleteBtn.classList.add('hidden');
                    currentEditingOrder = null;

                    // Перезагружаем только если изменился адрес
                    if (currentValues.address.trim() !== addressEl.dataset.originalAddress?.trim()) {
                        window.location.reload();
                    }
                } else {
                    const error = await res.json();
                    alert(error.message || 'Ошибка при сохранении');
                }
            } catch (e) {
                console.error(e);
                alert('Ошибка соединения. Проверьте интернет и попробуйте снова.');
            }
        }
    });

    deleteBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (confirm('Вы уверены, что хотите удалить этот заказ?')) {
            try {
                const res = await fetch(`/api/orders/${order.id}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    }
                });

                if (res.ok) {
                    map.geoObjects.remove(mark);
                    item.remove();
                    const ordersCount = document.getElementById('orders-count');
                    ordersCount.textContent = parseInt(ordersCount.textContent) - 1;
                } else {
                    const error = await res.json();
                    alert(error.message || 'Ошибка при удалении заказа');
                }
            } catch (err) {
                console.error('Ошибка удаления:', err);
                alert(`Ошибка при удалении заказа: ${err.message}`);
            }
        }
    });
}

// === Инициализация карты и заказов ===
function initializeOrders(map, courierOrders, courierData) {
    const ordersList = document.getElementById('orders-list');
    const filterBlock = document.getElementById('courier-filter-buttons');
    const courierSearch = document.getElementById('courier-search');
    let colorIndex = 0;
    const allPlacemarks = [];
    const courierPlacemarks = {};

    function setActiveCourier(id) {
        if (id === 'all') {
            allPlacemarks.forEach(({ mark }) => mark.options.set('visible', true));
        } else {
            allPlacemarks.forEach(({ mark }) => {
                const courierId = mark.properties.get('courierId');
                mark.options.set('visible', courierId === id || courierId === 'no_courier');
            });
        }

        document.querySelectorAll('.order-item').forEach(el => {
            el.style.display = (id === 'all' || el.dataset.courier === id || el.dataset.courier === 'no_courier')
                ? 'block'
                : 'none';
        });
    }

    // Инициализация заказов без курьера
    if (courierOrders['no_courier']) {
        courierOrders['no_courier'].forEach(order => {
            const item = createOrderItem(order, 'no_courier');
            const mark = createOrderMarker(map, order, 'no_courier');

            setupOrderClickHandler(item, order, mark, map);
            setupMarkerClickHandler(item, order, mark);
            setupEditButtonHandler(item, order, mark, map);

            allPlacemarks.push({ mark, order });
            ordersList.prepend(item);
        });
    }

    // Инициализация заказов с курьерами
    for (const [courierId, orders] of Object.entries(courierOrders)) {
        if (courierId === 'no_courier') continue;

        const data = courierData[courierId] || {};
        const color = courierColors[colorIndex++ % courierColors.length];

        // Создание кнопки фильтра для курьера
        const btn = document.createElement('button');
        btn.className = 'courier-btn';
        btn.textContent = data.name || courierId;
        btn.dataset.courier = courierId;

        btn.addEventListener('click', () => {
            document.querySelectorAll('.courier-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setActiveCourier(courierId);
        });

        filterBlock.appendChild(btn);
        courierPlacemarks[courierId] = [];

        // Инициализация заказов курьера
        orders.forEach(order => {
            const item = createOrderItem(order, courierId, color);
            const mark = createOrderMarker(map, order, courierId, color);

            setupOrderClickHandler(item, order, mark, map);
            setupMarkerClickHandler(item, order, mark);
            setupEditButtonHandler(item, order, mark, map);

            courierPlacemarks[courierId].push({ mark, order });
            allPlacemarks.push({ mark, order });
            ordersList.appendChild(item);
        });
    }

    document.getElementById('orders-count').textContent = Object.values(courierOrders).flat().length;

    // Инициализация кнопки "Все"
    const allBtn = document.querySelector('.courier-btn.active[data-courier="all"]');
    allBtn.addEventListener('click', () => {
        document.querySelectorAll('.courier-btn').forEach(btn =>
            btn.classList.toggle('active', btn.dataset.courier === 'all')
        );
        setActiveCourier('all');
    });

    // Поиск курьеров
    courierSearch.addEventListener('input', () => {
        const val = courierSearch.value.toLowerCase();
        document.querySelectorAll('.courier-btn').forEach(btn => {
            const name = btn.textContent.toLowerCase();
            btn.style.display = name.includes(val) ? 'block' : 'none';
        });
    });
}

// === Инициализация карты Yandex ===
ymaps.ready(() => {
    const map = new ymaps.Map("map", {
        center: depotCoords,
        zoom: 14,
        controls: [],
        suppressMapOpenBlock: true
    });

    addWarehouseToMap(map, depotCoords);
    initializeOrders(map, courierOrders, courierData);

    // Поиск адресов
    const addressInput = document.getElementById('address-search');
    const addressBtn = document.getElementById('address-search-btn');

    addressBtn.addEventListener('click', () => searchAddress(map, addressInput.value));
    addressInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') searchAddress(map, addressInput.value);
    });
});

// === Поиск заказов ===
const orderSearch = document.getElementById('order-search');
if (orderSearch) {
    orderSearch.addEventListener('input', () => {
        const query = orderSearch.value.toLowerCase();
        document.querySelectorAll('.order-item').forEach(order => {
            const orderText = order.textContent.toLowerCase();
            order.style.display = orderText.includes(query) ? 'block' : 'none';
        });
    });
}

// === Управление курьерами ===
document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.clstr-courier');
    if (!btn) return;

    e.preventDefault();
    const courierId = btn.dataset.id;
    const action = btn.dataset.action;
    const projectId = window.location.pathname.split('/')[2];

    try {
        window.location.hash = 'couriers';

        if (action === 'kick') {
            if (!confirm("Вы уверены, что хотите удалить этого курьера?")) return;

            const res = await fetch(`/api/users/${courierId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            if (res.ok) {
                window.location.reload(true);
            } else {
                const error = await res.json();
                alert(error.message || 'Ошибка при удалении');
            }

        } else if (action === 'add' || action === 'remove') {
            const method = action === 'add' ? 'POST' : 'DELETE';
            const res = await fetch('/api/courier_relations', {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                credentials: 'include',
                body: JSON.stringify({
                    project_id: parseInt(projectId),
                    courier_id: parseInt(courierId)
                })
            });

            if (res.ok) {
                window.location.reload(true);
            } else {
                const error = await res.json();
                alert(error.message || `Ошибка при ${action === 'add' ? 'добавлении' : 'удалении'}`);
            }
        }
    } catch (err) {
        console.error('Ошибка:', err);
        alert('Ошибка сети: ' + err.message);
    }
});

// === Кластеризация ===
clusteringbtn?.addEventListener("click", async () => {
    const clusteringModal = new bootstrap.Modal(document.getElementById('clusteringModal'));
    const loadingBlock = document.getElementById('clustering-loading');
    const successBlock = document.getElementById('clustering-success');
    const errorBlock = document.getElementById('clustering-error');
    const errorMessage = document.getElementById('clustering-error-message');

    loadingBlock.style.display = 'block';
    successBlock.style.display = 'none';
    errorBlock.style.display = 'none';
    clusteringSuccess = false;
    clusteringModal.show();

    try {
        const response = await fetch(window.location.pathname, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ start_clustering: true })
        });

        if (response.ok) {
            loadingBlock.style.display = 'none';
            successBlock.style.display = 'block';
            clusteringSuccess = true;
        } else {
            const error = await response.json();
            loadingBlock.style.display = 'none';
            errorMessage.textContent = error.message || "Произошла ошибка на сервере.";
            errorBlock.style.display = 'block';
        }
    } catch (error) {
        loadingBlock.style.display = 'none';
        errorMessage.textContent = "Сетевая ошибка. Проверьте соединение.";
        errorBlock.style.display = 'block';
        console.error(error);
    }
});

document.getElementById('clusteringModal')?.addEventListener('hidden.bs.modal', () => {
    if (clusteringSuccess) {
        window.location.reload();
    }
});

// === Управление складом ===
document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('storageModalOverlay');
    if (!overlay) return;

    const input = document.getElementById('storageInput');
    const button = document.getElementById('saveStorageBtn');
    const modal = new bootstrap.Modal(overlay);

    function flashError() {
        input.classList.add('error');
        input.focus();
        setTimeout(() => input.classList.remove('error'), 1000);
    }

    button.addEventListener('click', async function() {
        const address = input.value.trim();
        if (!address) {
            flashError();
            return;
        }

        try {
            const projectId = window.location.pathname.split('/').pop();
            const response = await fetch(`/api/projects/${projectId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ storage: address })
            });

            if (response.ok) {
                modal.hide();
                window.location.reload();
            } else {
                flashError();
            }
        } catch (error) {
            console.error('Ошибка:', error);
            flashError();
        }
    });
});

// === Функция для обработки добавления нового заказа ===
function setupAddOrderButton() {
    const addOrderBtn = document.getElementById('add-order-btn');
    const ordersList = document.getElementById('orders-list');

    if (!addOrderBtn || !ordersList) return;

    addOrderBtn.addEventListener('click', () => {
        // Проверяем, нет ли уже создаваемого заказа
        if (document.querySelector('.order-item.new-order') || currentEditingOrder) {
            return;
        }

        // Блокируем другие заказы
        document.querySelectorAll('.order-item').forEach(item => {
            if (!item.classList.contains('new-order')) {
                item.style.pointerEvents = 'none';
                item.style.opacity = '0.7';
            }
        });

        const newOrderItem = createNewOrderItem();
        ordersList.prepend(newOrderItem);

        // Фокусируемся на поле адреса
        newOrderItem.querySelector('.new-order-input').focus();

        // Обработчик сохранения
        const saveBtn = newOrderItem.querySelector('.save-new-order-btn');
        saveBtn.addEventListener('click', async () => {
        const inputs = newOrderItem.querySelectorAll('.new-order-input');
        const [addressInput, nameInput, phoneInput, analyticsIdInput, commentInput, priceInput] = inputs;

        // Проверяем обязательные поля
        if (!addressInput.value.trim() || !phoneInput.value.trim() || !nameInput.value.trim() || !priceInput.value.trim()) {
            alert('Адрес, телефон, цена и имя обязательны для заполнения');
            return;
        }

        // Получаем project_id из URL
        const pathParts = window.location.pathname.split('/');
        const projectId = pathParts[2];

        // Формируем данные для отправки
        const orderData = {
            phone: phoneInput.value.trim(),
            name: nameInput.value.trim(),
            address: addressInput.value.trim(),
            project_id: parseInt(projectId),
            price: priceInput.value.trim() ? parseInt(priceInput.value.trim()) : 0,
            comment: commentInput.value.trim() || null,
            analytics_id: analyticsIdInput.value.trim() || null,
            who_delivers: -1
        };

        try {
            const response = await fetch('/api/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(orderData)
            });

            if (!response.ok) {
                const error = await response.json();
                alert(error.message || 'Ошибка при создании заказа');
                return;
            }

            window.location.reload();
        } catch (err) {
            console.error('Ошибка:', err);
            alert('Ошибка соединения. Проверьте интернет и попробуйте снова.');
        }

        document.querySelectorAll('.order-item').forEach(item => {
                item.style.pointerEvents = '';
                item.style.opacity = '';
                });
    });

        // Обработчик отмены
        const cancelBtn = newOrderItem.querySelector('.cancel-new-order-btn');
        cancelBtn.addEventListener('click', () => {
            newOrderItem.remove();
            // Разблокируем заказы после отмены
            document.querySelectorAll('.order-item').forEach(item => {
                item.style.pointerEvents = '';
                item.style.opacity = '';
            });
        });
    });
}


document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('hiddenFileInput');
    if (input) {
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                const form = document.getElementById('importForm');
                const fileInput = document.getElementById('actualFileInput');

                // Передаем выбранный файл в форму
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(this.files[0]);
                fileInput.files = dataTransfer.files;

                form.submit();
            }
        });
    }
});


document.addEventListener('DOMContentLoaded', function() {
    const importBtn = document.querySelector('.import-btn');
    const impTitle = document.querySelector('.imp-title');
    let hideTimeout;

    // Показываем при наведении
    importBtn.addEventListener('mouseenter', function() {
        clearTimeout(hideTimeout);
        impTitle.classList.remove('hidden');
    });

    // Скрываем через 2 секунды после ухода курсора
    importBtn.addEventListener('mouseleave', function() {
        hideTimeout = setTimeout(() => {
            impTitle.classList.add('hidden');
        }, 2000);
    });

    // Если курсор перешел на подсказку - отменяем скрытие
    impTitle.addEventListener('mouseenter', function() {
        clearTimeout(hideTimeout);
    });

    // При уходе с подсказки - скрываем через 2 секунды
    impTitle.addEventListener('mouseleave', function() {
        hideTimeout = setTimeout(() => {
            impTitle.classList.add('hidden');
        }, 2000);
    });
});



// === Инициализация при загрузке ===
document.addEventListener('DOMContentLoaded', () => {
    setupAddOrderButton();
    if (window.location.hash === '#couriers') {
        switchToCouriersTab();
        history.replaceState(null, null, ' ');
    }
});
