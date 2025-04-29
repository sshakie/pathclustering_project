document.addEventListener("DOMContentLoaded", function () {
  const courierData = {
    courier_1: { name: 'Иван Иванов', phone: '+79991234567', whatsapp: '@ivan_w', telegram: '@ivan_t' },
    courier_2: { name: 'Мария Смирнова', phone: '+79997654321', whatsapp: '@maria_w', telegram: '@maria_t' }
  };

  const courierOrders = {
    courier_1: [
      { id: 1, address: "ул. Пушкина д.111", price: "1537 руб.", coords: [55.750, 37.610], analytics_id: "arf137" },
      { id: 2, address: "ул. Космонавтов д.84", price: "17 руб.", coords: [55.751, 37.612], analytics_id: "bhg036" }
    ],
    courier_2: [
      { id: 3, address: "ул. Вершишева д.51", price: "191 руб.", coords: [55.752, 37.608], analytics_id: "abc012" }
    ]
  };

  const courierColors = ['#ff4d4d', '#4dd2ff', '#85e085', '#ffcc66', '#cc99ff', '#9966cc', '#ff9966'];

  // === TAB переключатели ===
  const tabMap = document.getElementById("tab-map");
  const tabCouriers = document.getElementById("tab-couriers");

  const addressWrapper = document.getElementById("address-search-wrapper");
  const mapWrapper = document.getElementById("map-wrapper");
  const couriers = document.getElementById("couriers");

  function activateTab(tab) {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
  }

  tabMap.addEventListener("click", () => {
  activateTab(tabMap);
  addressWrapper.classList.remove("hidden");
  mapWrapper.classList.remove("hidden");
  couriers.classList.add("hidden");
});

tabCouriers.addEventListener("click", () => {
  activateTab(tabCouriers);
  addressWrapper.classList.add("hidden");
  mapWrapper.classList.add("hidden");
  couriers.classList.remove("hidden");
});

  // === ИНИЦИАЛИЗАЦИЯ КАРТЫ ===
  ymaps.ready(init);

  function init() {
    const map = new ymaps.Map("map", {
      center: [55.751, 37.61],
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
      document.querySelectorAll('.courier-section').forEach(sec =>
        sec.classList.remove('expanded')
      );
      setActiveCourier('all');
    });

    for (const [courierId, orders] of Object.entries(courierOrders)) {
      const data = courierData[courierId] || {};
      const color = courierColors[colorIndex++ % courierColors.length];

      const section = document.createElement('div');
      section.className = 'courier-section';

      const btn = document.createElement('button');
      btn.className = 'courier-btn';
      btn.textContent = data.name || courierId;
      btn.dataset.courier = courierId;

      btn.addEventListener('click', () => {
        document.querySelectorAll('.courier-section').forEach(sec =>
          sec.classList.remove('expanded')
        );
        document.querySelectorAll('.courier-btn').forEach(b =>
          b.classList.remove('active')
        );
        btn.classList.add('active');
        section.classList.add('expanded');
        setActiveCourier(courierId);
      });

      section.appendChild(btn);
      filterBlock.appendChild(section);

      courierPlacemarks[courierId] = [];

    orders.forEach(order => {
      const item = document.createElement('div');
      item.className = 'order-item';
      item.dataset.id = order.id;
      item.dataset.courier = courierId;
      item.innerHTML = `
  <div style="font-weight: bold;">№ ${order.analytics_id}</div>
  <div>${order.address}</div>
  <div style="color: orangered; font-weight: 700; text-align: right;">${order.price}</div>`;
      ordersList.appendChild(item);

        const mark = new ymaps.Placemark(order.coords, {
          balloonContent: order.address,
          hintContent: data.name || courierId
        }, {
          preset: 'islands#circleIcon',
          iconColor: color
        });

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
        document.querySelectorAll('.order-item').forEach(el => el.style.display = 'block');
        return;
      }

      for (const [courier, items] of Object.entries(courierPlacemarks)) {
        items.forEach(({ mark }) => {
          const visible = courier === id;
          mark.options.set('visible', visible);
        });
      }

      document.querySelectorAll('.order-item').forEach(el => {
        el.style.display = el.dataset.courier === id ? 'block' : 'none';
      });
    }

    // поиск курьера по имени
    courierSearch.addEventListener('input', () => {
      const val = courierSearch.value.toLowerCase();
      document.querySelectorAll('.courier-section').forEach(section => {
        const name = section.querySelector('.courier-btn')?.textContent.toLowerCase() || '';
        const infoText = section.querySelector('.courier-info')?.textContent.toLowerCase() || '';
        const match = name.includes(val) || infoText.includes(val);
        section.style.display = match ? 'block' : 'none';
      });
    });

    // поиск адреса
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
          map.balloon.open(coords, name, { closeButton: true });
        } else {
          alert("Адрес не найден.");
        }
      });
    }
  }
});
