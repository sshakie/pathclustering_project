console.log(courierOrders)

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
        <div><b>Комментарий:</b> ${order.comment || '—'}</div>
        <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
          <button class="delete-order-btn" style="background: #ff4d4d; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Удалить заказ</button>
        </div>
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
        const deleteBtn = item.querySelector('.delete-order-btn');

        // Если клик по кнопке редактирования/удаления или идет редактирование - не обрабатываем
        if (e.target.classList.contains('edit-btn') ||
            e.target.classList.contains('delete-order-btn') ||
            editBtn.textContent === '✅') {
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

    // Добавляем обработчик для кнопки удаления
    const deleteBtn = item.querySelector('.delete-order-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm('Вы уверены, что хотите удалить этот заказ?')) {
                try {
                    const res = await fetch(`/api/delete/${order.id}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken()
                        }
                    });

                    if (res.ok) {
                        // Удаляем маркер с карты
                        map.geoObjects.remove(mark);
                        // Удаляем элемент из списка
                        item.remove();
                        // Обновляем счетчик заказов
                        document.getElementById('orders-count').textContent =
                            parseInt(document.getElementById('orders-count').textContent) - 1;
                    } else {
                        const error = await res.json();
                        alert(error.message || 'Ошибка при удалении заказа');
                    }
                } catch (err) {
                    console.error('Ошибка:', err);
                    alert('Ошибка сети: ' + err.message);
                }
            }
        });
    }
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
        const commentEl = details.querySelector('div:nth-child(3)');

        if (!isEditing) {
            const nameVal = nameEl.textContent.replace('Имя:', '').trim();
            const phoneVal = phoneEl.textContent.replace('Телефон:', '').trim();
            const commentVal = commentEl.textContent.replace('Комментарий:', '').trim();
            const priceVal = priceEl.textContent.replace('руб.', '').trim();
            const addressVal = addressEl.textContent.trim();
            editBtn.dataset.editing = "true";

            item.dataset.tempAddress = addressVal;

            nameEl.innerHTML = `<b>Имя:</b> <input type="text" value="${nameVal}" class="edit-field">`;
            phoneEl.innerHTML = `<b>Телефон:</b> <input type="text" value="${phoneVal}" class="edit-field">`;
            commentEl.innerHTML = `<b>Комментарий:</b> <input type="text" value="${commentVal}" class="edit-field">`;
            priceEl.innerHTML = `<input type="number" value="${parseInt(priceVal)}" class="edit-field price-field"> руб.`;
            addressEl.innerHTML = `<input type="text" value="${addressVal}" class="edit-field address-field">`;

            editBtn.textContent = '✅';
            details.classList.remove('hidden');
            isEditing = true;
        } else {
            delete editBtn.dataset.editing;
            const updatedName = nameEl.querySelector('input').value;
            const updatedPhone = phoneEl.querySelector('input').value;
            const updatedComment = commentEl.querySelector('input').value;
            const updatedPrice = priceEl.querySelector('input').value;
            const updatedAddress = addressEl.querySelector('input').value;

            try {
                const res = await fetch(`/api/orders/${order.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: updatedName,
                        phone: updatedPhone,
                        comment: updatedComment,
                        price: parseInt(updatedPrice),
                        address: updatedAddress
                    }),
                });

                if (res.ok) {
                    nameEl.innerHTML = `<b>Имя:</b> ${updatedName || '—'}`;
                    phoneEl.innerHTML = `<b>Телефон:</b> ${updatedPhone || '—'}`;
                    commentEl.innerHTML = `<b>Комментарий:</b> ${updatedComment || '—'}`;
                    priceEl.innerHTML = `${updatedPrice} руб.`;
                    addressEl.innerHTML = updatedAddress;

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
      const comment = order.querySelector('.order-details b:nth-child(3)')?.nextSibling?.textContent?.toLowerCase() || '';
      const address = order.querySelector('.order-header div:nth-child(2)')?.textContent?.toLowerCase() || '';
      const analyticsId = order.querySelector('.order-header div:nth-child(1)')?.textContent?.toLowerCase() || '';

      const match = [name, phone, comment, address, analyticsId].some(text => text.includes(query));
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

document.addEventListener('DOMContentLoaded', function() {
    // Получаем текущий URL страницы без параметров запроса
    const currentPageUrl = window.location.origin + window.location.pathname;

    // Используем courierData для данных о курьерах
    const exportType = document.getElementById('exportType');
    const steps = {
        'initial': document.getElementById('step1'),
        'orders': document.getElementById('step2-orders'),
        'couriers-type': document.getElementById('step2-couriers'),
        'couriers-select': document.getElementById('step3-couriers-select'),
        'couriers-format': document.getElementById('step3-couriers-format'),
        'couriers-export': document.getElementById('step4-couriers')
    };

    // Скрываем все шаги кроме первого
    function resetSteps() {
        for (const key in steps) {
            if (key !== 'initial') {
                steps[key].style.display = 'none';
            }
        }
    }

    // Генерация списка курьеров из courierData
    function generateCouriersList() {
        const container = document.getElementById('couriersCheckboxList');
        container.innerHTML = '';

        if (!courierData || typeof courierData !== 'object') {
            container.innerHTML = '<div class="alert alert-danger">Ошибка загрузки данных о курьерах</div>';
            return;
        }

        // Сортируем курьеров по имени
        const sortedCouriers = Object.entries(courierData).sort((a, b) => {
            const nameA = a[1].name || '';
            const nameB = b[1].name || '';
            return nameA.localeCompare(nameB);
        });

        // Создаем чекбоксы для каждого курьера
        for (const [id, courier] of sortedCouriers) {
            const div = document.createElement('div');
            div.className = 'form-check mb-2';

            const input = document.createElement('input');
            input.className = 'form-check-input courier-checkbox';
            input.type = 'checkbox';
            input.value = id;
            input.id = `courier-${id}`;
            input.dataset.name = courier.name || `Курьер ${id}`;

            const label = document.createElement('label');
            label.className = 'form-check-label';
            label.htmlFor = `courier-${id}`;
            label.textContent = courier.name || `Курьер ${id}`;

            div.appendChild(input);
            div.appendChild(label);
            container.appendChild(div);
        }

        if (Object.keys(courierData).length === 0) {
            container.innerHTML = '<div class="alert alert-warning">Нет доступных курьеров</div>';
        }
    }

    // Обработчики событий
    exportType.addEventListener('change', function() {
        resetSteps();
        if (this.value === 'orders') {
            steps['orders'].style.display = 'block';
        } else if (this.value === 'couriers') {
            steps['couriers-type'].style.display = 'block';
            generateCouriersList();
        }
    });

    document.getElementById('couriersExportType').addEventListener('change', function() {
        if (this.value === 'selected') {
            steps['couriers-select'].style.display = 'block';
            steps['couriers-format'].style.display = 'none';
            steps['couriers-export'].style.display = 'none';
        } else {
            steps['couriers-select'].style.display = 'none';
            steps['couriers-format'].style.display = 'block';
        }
    });

    document.getElementById('couriersCheckboxList').addEventListener('change', function() {
        const anyChecked = document.querySelectorAll('#couriersCheckboxList input[type="checkbox"]:checked').length > 0;
        steps['couriers-format'].style.display = anyChecked ? 'block' : 'none';
        steps['couriers-export'].style.display = 'none';
    });

    document.getElementById('exportFormat').addEventListener('change', function() {
        steps['couriers-export'].style.display = 'block';
    });

    document.getElementById('exportOrdersBtn').addEventListener('click', function() {
        exportData('orders');
    });

    document.getElementById('exportCouriersBtn').addEventListener('click', function() {
        const exportType = document.getElementById('couriersExportType').value;
        const exportFormat = document.getElementById('exportFormat').value;
        const selectedCouriers = [];

        if (exportType === 'selected') {
            document.querySelectorAll('#couriersCheckboxList input[type="checkbox"]:checked').forEach(checkbox => {
                selectedCouriers.push({
                    id: checkbox.value,
                    name: checkbox.dataset.name
                });
            });

            if (selectedCouriers.length === 0) {
                showAlert('Пожалуйста, выберите хотя бы одного курьера', 'warning');
                return;
            }
        }

        exportData('couriers', {
            couriersType: exportType,
            format: exportFormat,
            selectedCouriers: selectedCouriers,
            allCouriers: exportType === 'all' ? courierData : null
        });
    });

    // Функция экспорта с отправкой на текущий URL
    function exportData(type, options = {}) {
    fetch(currentPageUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({
            action: 'export',
            type: type,
            data: options
        })
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.blob().then(blob => {
            // Попробуем вытащить имя файла из заголовка
            const disposition = response.headers.get('Content-Disposition');
            let fileName = 'exported_file.xlsx';

            if (disposition && disposition.includes('filename=')) {
                const match = disposition.match(/filename="?([^"]+)"?/);
                if (match && match[1]) {
                    fileName = decodeURIComponent(match[1]);
                }
            }

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            bootstrap.Modal.getInstance(document.getElementById('ExportModal')).hide();
            showAlert('Экспорт завершен успешно!', 'success');
        });
    })
    .catch(error => {
        console.error('Ошибка экспорта:', error);
        showAlert(`Ошибка при экспорте: ${error.message}`, 'danger');
    });
}



    // Вспомогательная функция для показа уведомлений
    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.prepend(alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    }
});