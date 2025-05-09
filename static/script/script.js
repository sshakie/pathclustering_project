const courierColors = ['#ff4d4d', '#4dd2ff', '#85e085', '#ffcc66', '#cc99ff', '#9966cc', '#ff9966'];
const depotCoords = [52.605003, 39.535107]
// === TAB переключатели ===
const tabMap = document.getElementById("tab-map");
const tabCouriers = document.getElementById("tab-couriers");

const addressWrapper = document.getElementById("address-search-wrapper");
const mapWrapper = document.getElementById("map-wrapper");
const couriers = document.getElementById("couriers");
const exportbtn = document.getElementById("exportbtn");
const clusteringbtn = document.getElementById("clusteringbtn");

function activateTab(tab) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  tab.classList.add("active");
}

tabMap.addEventListener("click", () => {
  activateTab(tabMap);
  addressWrapper.classList.remove("hidden");
  mapWrapper.classList.remove("hidden");
  couriers.classList.add("hidden");
  exportbtn.classList.remove("hidden");
  clusteringbtn.classList.remove("hidden");
});

tabCouriers.addEventListener("click", () => {
  activateTab(tabCouriers);
  addressWrapper.classList.add("hidden");
  mapWrapper.classList.add("hidden");
  couriers.classList.remove("hidden");
  exportbtn.classList.add("hidden");
  clusteringbtn.classList.add("hidden");
});

// === ИНИЦИАЛИЗАЦИЯ КАРТЫ ===
ymaps.ready(init);

function init() {
  const map = new ymaps.Map("map", {
    center: [52.605003, 39.535107],
    zoom: 14,
    controls: [],
    suppressMapOpenBlock: true
  });

  const ordersList = document.getElementById('orders-list');
  const filterBlock = document.getElementById('courier-filter-buttons');
  const courierSearch = document.getElementById('courier-search');

  let colorIndex = 0;
  const allPlacemarks = [];
  const courierPlacemarks = {};

  // Универсальная функция для создания элемента заказа
  function createOrderItem(order, courierId, color) {
    const item = document.createElement('div');
    item.className = courierId === 'no_courier' ? 'order-item unassigned' : 'order-item';
    item.dataset.id = order.id;
    item.dataset.courier = courierId;

    const orderNumber = order.analytics_id ? order.analytics_id : order.id;

    item.innerHTML = `
      <div class="order-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-weight: bold;">№ ${orderNumber}</div>
          <button class="edit-btn">✏️</button>
        </div>
        <div class="order-address">${order.address}</div>
      </div>
      <div class="order-details hidden">
        <div><b>Имя:</b> ${order.name || '—'}</div>
        <div><b>Телефон:</b> ${order.phone || '—'}</div>
        <div><b>Координаты:</b> [${order.coords.join(', ')}]</div>
      </div>
      <div class="order-price" style="color: orangered; font-weight: 700; text-align: right;">${order.price} руб.</div>
    `;

    return item;
  }

  // Универсальная функция для создания маркера
  function createOrderMarker(order, courierId, color) {
    const mark = new ymaps.Placemark(order.coords, {
      balloonContent: order.address,
      hintContent: courierId === 'no_courier' ? 'Не назначен' : (courierData[courierId]?.name || courierId)
    }, {
      preset: 'islands#circleIcon',
      iconColor: courierId === 'no_courier' ? '#808080' : color,
      balloonAutoPan: false,
      hideIconOnBalloonOpen: false
    });

    mark.properties.set('courierId', courierId);
    map.geoObjects.add(mark);
    return mark;
  }

  // Универсальный обработчик кликов по заказу
  function setupOrderClickHandler(item, order, mark) {
    item.addEventListener('click', (e) => {
        // Получаем кнопку редактирования этого заказа
        const editBtn = item.querySelector('.edit-btn');

        // Если клик по кнопке редактирования или идет редактирование - не обрабатываем
        if (e.target.classList.contains('edit-btn') || editBtn.textContent === '✅') {
            return;
        }

        // Если где-то идет редактирование - не закрываем детали
        const isAnyEditing = document.querySelector('.edit-btn[data-editing="true"]');
        if (isAnyEditing) return;

        // Закрываем все открытые details, кроме текущего
        document.querySelectorAll('.order-details:not(.hidden)').forEach(openDetails => {
            if (openDetails !== item.querySelector('.order-details')) {
                openDetails.classList.add('hidden');
                const parentItem = openDetails.closest('.order-item');
                if (parentItem) {
                    parentItem.querySelector('.edit-btn').style.display = 'none';
                }
            }
        });

        const details = item.querySelector('.order-details');
        details.classList.toggle('hidden');

        // Управляем видимостью кнопки редактирования
        editBtn.style.display = details.classList.contains('hidden') ? 'none' : 'block';

        // Центрируем карту и открываем балун
        map.setCenter(order.coords);
        mark.balloon.open();
        highlightOrder(order.id);
    });
}

  // Обработчик кликов по маркеру
  function setupMarkerClickHandler(item, order, mark) {
    mark.events.add('click', () => {
      item.click(); // Эмулируем клик по элементу заказа
    });
  }

  // Обработчик кнопки редактирования (с оригинальным стилем полей)
  function setupEditButtonHandler(item, order, mark) {
    const editBtn = item.querySelector('.edit-btn');
    const details = item.querySelector('.order-details');
    const addressEl = item.querySelector('.order-address');
    const priceEl = item.querySelector('.order-price');

    let isEditing = false;

    editBtn.addEventListener('click', async (e) => {
      e.stopPropagation();

      const nameEl = details.querySelector('div:nth-child(1)');
      const phoneEl = details.querySelector('div:nth-child(2)');

      if (!isEditing) {
        const nameVal = nameEl.textContent.replace('Имя:', '').trim();
        const phoneVal = phoneEl.textContent.replace('Телефон:', '').trim();
        const priceVal = priceEl.textContent.replace('руб.', '').trim();
        const addressVal = addressEl.textContent.trim();
        editBtn.dataset.editing = "true";

        item.dataset.tempAddress = addressVal;

        // Оригинальный стиль полей ввода как у вас было
        nameEl.innerHTML = `<b>Имя:</b> <input type="text" value="${nameVal}" style="border:none; border-bottom: 1px solid #aaa; outline:none; background:none; font-size:14px; width:70%;">`;phoneEl.innerHTML = `<b>Телефон:</b> <input type="text" value="${phoneVal}" style="border:none; border-bottom: 1px solid #aaa; outline:none; background:none; font-size:14px; width:70%;">`;
        priceEl.innerHTML = `<input type="number" value="${parseInt(priceVal)}" style="border:none; border-bottom: 1px solid #aaa; outline:none; background:none; font-weight:700; text-align:right; width:60%;"> руб.`;
        addressEl.innerHTML = `<input type="text" value="${addressVal}" style="border:none; border-bottom: 1px solid #aaa; outline:none; background:none; font-size:14px; width:100%;">`;

        editBtn.textContent = '✅';
        details.classList.remove('hidden');
        isEditing = true;
      } else {
        delete editBtn.dataset.editing;
        const updatedName = nameEl.querySelector('input').value;
        const updatedPhone = phoneEl.querySelector('input').value;
        const updatedPrice = priceEl.querySelector('input').value;
        const updatedAddress = addressEl.querySelector('input').value;

        try {
          const res = await fetch(`/api/orders/${order.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: updatedName,
              phone: updatedPhone,
              price: parseInt(updatedPrice),
              address: updatedAddress
            }),
          });

          if (res.ok) {
            nameEl.innerHTML = `<b>Имя:</b> ${updatedName}`;
            phoneEl.innerHTML = `<b>Телефон:</b> ${updatedPhone}`;
            priceEl.innerHTML = `${updatedPrice} руб.`;
            addressEl.innerHTML = updatedAddress;

            // Обновляем маркер на карте
            mark.properties.set('balloonContent', updatedAddress);

            editBtn.textContent = '✏️';
            isEditing = false;
          } else {
            addressEl.innerHTML = item.dataset.tempAddress || order.address;
            alert('Ошибка при сохранении');
          }
        } catch (e) {
          console.error(e);
          addressEl.innerHTML = item.dataset.tempAddress || order.address;
          alert('Ошибка соединения');
        }
      }
    });
  }

  // Инициализация всех заказов
  function initializeOrders() {
    // Заказы без курьера
    if (courierOrders['no_courier']) {
      courierOrders['no_courier'].forEach(order => {
        const item = createOrderItem(order, 'no_courier');
        const mark = createOrderMarker(order, 'no_courier');

        setupOrderClickHandler(item, order, mark);
        setupMarkerClickHandler(item, order, mark);
        setupEditButtonHandler(item, order, mark);

        allPlacemarks.push({ mark, order });
        ordersList.prepend(item);
      });
    }

    // Заказы с курьерами
    for (const [courierId, orders] of Object.entries(courierOrders)) {
      if (courierId === 'no_courier') continue;

      const data = courierData[courierId] || {};
      const color = courierColors[colorIndex++ % courierColors.length];

      // Создаем кнопку фильтра для курьера
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

      // Инициализируем заказы курьера
      orders.forEach(order => {
        const item = createOrderItem(order, courierId, color);
        const mark = createOrderMarker(order, courierId, color);

        setupOrderClickHandler(item, order, mark);
        setupMarkerClickHandler(item, order, mark);
        setupEditButtonHandler(item, order, mark);

        courierPlacemarks[courierId].push({ mark, order });
        allPlacemarks.push({ mark, order });
        ordersList.appendChild(item);
      });
    }

    document.getElementById('orders-count').textContent =
      Object.values(courierOrders).flat().length;
  }

  // Инициализация кнопки "Все"
  const allBtn = document.querySelector('.courier-btn.active[data-courier="all"]');
  allBtn.addEventListener('click', () => {
    document.querySelectorAll('.courier-btn').forEach(btn =>
      btn.classList.toggle('active', btn.dataset.courier === 'all')
    );
    setActiveCourier('all');
  });
    addWarehouseToMap(depotCoords)
   function addWarehouseToMap(coords) {
    const warehousePlacemark = new ymaps.Placemark(
    coords,
    {
      hintContent: 'Склад',
      balloonContent: 'Склад. Отсюда будут забирать заказы.'
    },
    {
      preset: 'islands#blackDeliveryCircleIcon',
      iconColor: '#000000'}
  );

  map.geoObjects.add(warehousePlacemark);
  return warehousePlacemark;
}
  function highlightOrder(id) {
    document.querySelectorAll('.order-item').forEach(el =>
      el.classList.toggle('active', el.dataset.id == id)
    );
  }

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
      if (id === 'all') {
        el.style.display = 'block';
      } else {
        el.style.display = (el.dataset.courier === id || el.dataset.courier === 'no_courier') ? 'block' : 'none';
      }
    });
  }

  // Поиск курьеров
  courierSearch.addEventListener('input', () => {
    const val = courierSearch.value.toLowerCase();
    document.querySelectorAll('.courier-btn').forEach(btn => {
      const name = btn.textContent.toLowerCase();
      btn.style.display = name.includes(val) ? 'block' : 'none';
    });
  });

  // Поиск адресов
  const addressInput = document.getElementById('address-search');
  const addressBtn = document.getElementById('address-search-btn');

  addressBtn.addEventListener('click', () => searchAddress(addressInput.value));
  addressInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') searchAddress(addressInput.value);
  });

  function searchAddress(address) {
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

  // Запускаем инициализацию
  initializeOrders();
}

// Остальной код остается без изменений
const orderSearch = document.getElementById('order-search');

if (orderSearch) {
  orderSearch.addEventListener('input', () => {
    const query = orderSearch.value.toLowerCase();
    document.querySelectorAll('.order-item').forEach(order => {
      const name = order.querySelector('.order-details b:nth-child(1)')?.nextSibling?.textContent?.toLowerCase() || '';
      const phone = order.querySelector('.order-details b:nth-child(2)')?.nextSibling?.textContent?.toLowerCase() || '';
      const address = order.querySelector('.order-header div:nth-child(2)')?.textContent?.toLowerCase() || '';
      const analyticsId = order.querySelector('.order-header div:nth-child(1)')?.textContent?.toLowerCase() || '';

      const match = [name, phone, address, analyticsId].some(text => text.includes(query));
      order.style.display = match ? 'block' : 'none';
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  if (window.location.hash === '#couriers') {
    switchToCouriersTab();
    history.replaceState(null, null, ' ');
  }

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
          return;
        }
        const error = await res.json();
        alert(error.message || 'Ошибка при удалении');

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
          return;
        }
        const error = await res.json();
        alert(error.message || `Ошибка при ${action === 'add' ? 'добавлении' : 'удалении'}`);
      }
    } catch (err) {
      console.error('Ошибка:', err);
      alert('Ошибка сети: ' + err.message);
    }
  });

  function switchToCouriersTab() {
    document.getElementById('tab-map').classList.remove('active');
    document.getElementById('tab-couriers').classList.add('active');
    document.getElementById('map-wrapper').classList.add('hidden');
    document.getElementById('address-search-wrapper').classList.add('hidden');
    exportbtn.classList.add("hidden");
    clusteringbtn.classList.add("hidden");
    document.getElementById('couriers').classList.remove('hidden');
  }

  function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
  }
});

function copyInviteLink() {
  const input = document.getElementById('inviteLinkInput');
  const btn = document.querySelector('.invite-btn');

  input.select();
  input.setSelectionRange(0, 99999);

  document.execCommand('copy');

  btn.classList.add('copied');
  setTimeout(() => {
    btn.classList.remove('copied');
  }, 500);
}

let clusteringSuccess = false; // Флаг успешной кластеризации

clusteringbtn.addEventListener("click", async () => {
  const clusteringModalElement = document.getElementById('clusteringModal');
  const clusteringModal = new bootstrap.Modal(clusteringModalElement);

  const loadingBlock = document.getElementById('clustering-loading');
  const successBlock = document.getElementById('clustering-success');
  const errorBlock = document.getElementById('clustering-error');
  const errorMessage = document.getElementById('clustering-error-message');

  // Сброс состояний
  loadingBlock.style.display = 'block';
  successBlock.style.display = 'none';
  errorBlock.style.display = 'none';
  clusteringSuccess = false;

  clusteringModal.show();

  try {
    const response = await fetch(window.location.pathname, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ start_clustering: true })
    });

    if (response.ok) {
      const result = await response.json();
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

// Обновление страницы после успешной кластеризации при закрытии модалки
document.getElementById('clusteringModal').addEventListener('hidden.bs.modal', () => {
  if (clusteringSuccess) {
    window.location.reload();
  }
});
