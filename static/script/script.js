const courierColors = ['#ff4d4d', '#4dd2ff', '#85e085', '#ffcc66', '#cc99ff', '#9966cc', '#ff9966'];

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

  const allBtn = document.querySelector('.courier-btn.active[data-courier="all"]');
  allBtn.addEventListener('click', () => {
    document.querySelectorAll('.courier-btn').forEach(btn =>
      btn.classList.toggle('active', btn.dataset.courier === 'all')
    );
    setActiveCourier('all');
  });

  // Заказы без курьера
  if (courierOrders['no_courier']) {
    courierOrders['no_courier'].forEach(order => {
      const item = document.createElement('div');
      item.className = 'order-item unassigned';
      item.dataset.id = order.id;
      item.dataset.courier = 'no_courier';
      item.innerHTML = `
        <div class="order-header">
          <div style="font-weight: bold;">№ ${order.analytics_id}</div>
          <div>${order.address}</div>
        </div>
        <div class="order-details hidden">
          <div><b>Имя:</b> ${order.name || '—'}</div>
          <div><b>Телефон:</b> ${order.phone || '—'}</div>
          <div><b>Координаты:</b> [${order.coords.join(', ')}]</div>
        </div>
        <div class="order-price" style="color: orangered; font-weight: 700; text-align: right;">${order.price}</div>
      `;

      item.addEventListener('click', () => {
        const details = item.querySelector('.order-details');
        details.classList.toggle('hidden');
      });

      ordersList.prepend(item);

      const mark = new ymaps.Placemark(order.coords, {
          balloonContent: order.address,
          hintContent: 'Не назначен'
        }, {
          preset: 'islands#circleIcon',

          iconColor: '#808080',
          balloonAutoPan: false,
          hideIconOnBalloonOpen: false
        });

       mark.properties.set('courierId', 'no_courier');
      map.geoObjects.add(mark);
      allPlacemarks.push({ mark });

      mark.events.add('click', () => highlightOrder(order.id));
      item.addEventListener('click', () => {
        map.setCenter(order.coords);
        mark.balloon.open();
        highlightOrder(order.id);
      });
    });
  }

  // Заказы с курьерами
  for (const [courierId, orders] of Object.entries(courierOrders)) {
    if (courierId === 'no_courier') continue;

    const data = courierData[courierId] || {};
    const color = courierColors[colorIndex++ % courierColors.length];

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

    orders.forEach(order => {
      const item = document.createElement('div');
      item.className = 'order-item';
      item.dataset.id = order.id;
      item.dataset.courier = courierId;
      const orderNumber = order.analytics_id ? order.analytics_id : order.id;

      item.innerHTML = `
        <div class="order-header">
          <div style="font-weight: bold;">№ ${order.analytics_id}</div>
          <div>${order.address}</div>
        </div>
        <div class="order-details hidden">
          <div><b>Имя:</b> ${order.name || '—'}</div>
          <div><b>Телефон:</b> ${order.phone || '—'}</div>
          <div><b>Координаты:</b> [${order.coords.join(', ')}]</div>
        </div>
        <div class="order-price" style="color: orangered; font-weight: 700; text-align: right;">${orderNumber}</div>
      `;

      item.addEventListener('click', () => {
        const details = item.querySelector('.order-details');
        details.classList.toggle('hidden');
      });

      ordersList.appendChild(item);

      const mark = new ymaps.Placemark(order.coords, {
        balloonContent: order.address,
        hintContent: data.name || courierId
      }, {
        preset: 'islands#circleIcon',
        iconColor: color,
        balloonAutoPan: false
      });
       mark.properties.set('courierId', courierId);
      map.geoObjects.add(mark);
      courierPlacemarks[courierId].push({ mark });
      allPlacemarks.push({ mark });

      mark.events.add('click', () => highlightOrder(order.id));
      item.addEventListener('click', () => {
        map.setCenter(order.coords);
        mark.balloon.open();
        highlightOrder(order.id);
      });
    });
  }

  document.getElementById('orders-count').textContent =
    Object.values(courierOrders).flat().length;

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

  courierSearch.addEventListener('input', () => {
    const val = courierSearch.value.toLowerCase();
    document.querySelectorAll('.courier-btn').forEach(btn => {
      const name = btn.textContent.toLowerCase();
      btn.style.display = name.includes(val) ? 'block' : 'none';
    });
  });

  const addressInput = document.getElementById('address-search');
  const addressBtn = document.getElementById('address-search-btn');

  addressBtn.addEventListener('click', () => {
    searchAddress(addressInput.value);
  });

  addressInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      searchAddress(addressInput.value);
    }
  });

  function searchAddress(address) {
    if (!address.trim()) return;

    ymaps.geocode(address).then(result => {
      const firstGeoObject = result.geoObjects.get(0);

      if (firstGeoObject) {
        const coords = firstGeoObject.geometry.getCoordinates();
        const name = firstGeoObject.getAddressLine();

        map.setCenter(coords, 16);

        map.balloon.open(coords, name, {
          closeButton: true
        });
      } else {
        alert("Адрес не найден.");
      }
    });
  }
}

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