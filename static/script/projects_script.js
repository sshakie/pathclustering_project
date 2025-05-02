const container = document.getElementById('projects');

// Оригинальный код отрисовки существующих проектов (без изменений)
data.forEach((project, index) => {
    const panel = document.createElement('div');
    panel.className = 'panel';

    const iconWrapper = document.createElement('div');
    iconWrapper.className = 'icon-wrapper';

    const icon = document.createElement('img');
    icon.src = `/static/icon/${project.icon}.png`;
    iconWrapper.appendChild(icon);

    const left = document.createElement('div');
    left.style.display = 'flex';
    left.style.alignItems = 'center';

    const name = document.createElement('span');
    name.textContent = project.name;

    left.appendChild(iconWrapper);
    left.appendChild(name);

    const project_index = document.createElement('span');
    project_index.className = 'panel-number';
    project_index.textContent = index + 1;

    const close = document.createElement('span');
    close.innerHTML = '&times;';
    close.className = 'close-btn';

    panel.appendChild(left);
    panel.appendChild(project_index);
    panel.appendChild(close);
    container.appendChild(panel);

    close.onclick = (e) => {
        e.stopPropagation();
        fetch(`/api/projects/${project.id}`, {
            method: 'DELETE'
        }).then(response => {
            panel.remove();
            updateProjectIndices();
        }).catch(error => {
            console.error('Ошибка сети:', error);
        });
    };
});

function updateProjectIndices() {
    const container = document.getElementById('projects');
    const panels = container.querySelectorAll('.panel');
    panels.forEach((panel, i) => {
        const number = panel.querySelector('.panel-number');
        if (number) {
            number.textContent = i + 1;
        }
    });
}

// Исправленный код для добавления проекта
document.getElementById('add-project-btn').addEventListener('click', () => {
    // Создаем временную панель для ввода
    const tempPanel = document.createElement('div');
    tempPanel.className = 'panel';

    // Иконка (случайная от 1 до 5)
    const iconNumber = Math.floor(Math.random() * 4) + 1;
    const iconWrapper = document.createElement('div');
    iconWrapper.className = 'icon-wrapper';
    const icon = document.createElement('img');
    icon.src = `/static/icon/${iconNumber}.png`;
    iconWrapper.appendChild(icon);

    // Поле ввода
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Введите название';
    input.style.fontSize = '20px';
    input.style.border = 'none';
    input.style.outline = 'none';
    input.style.background = 'transparent';

    // Левая часть (иконка + input)
    const left = document.createElement('div');
    left.style.display = 'flex';
    left.style.alignItems = 'center';
    left.appendChild(iconWrapper);
    left.appendChild(input);

    // Номер проекта
    const projectIndex = document.createElement('span');
    projectIndex.className = 'panel-number';
    projectIndex.textContent = container.children.length + 1;

    // Кнопка закрыть
    const close = document.createElement('span');
    close.innerHTML = '&times;';
    close.className = 'close-btn';
    close.onclick = (e) => {
        e.stopPropagation();
        tempPanel.remove();
    };

    // Собираем панель
    tempPanel.appendChild(left);
    tempPanel.appendChild(projectIndex);
    tempPanel.appendChild(close);
    container.appendChild(tempPanel);

    // Фокус на поле ввода
    input.focus();

    // Обработчик нажатия Enter
    input.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            const name = input.value.trim();
            if (!name) return;

            try {
                // Отправляем запрос на сервер
                const response = await fetch('/api/projects', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: name,
                        icon: iconNumber
                    })
                });

                if (!response.ok) {
                    throw new Error('Ошибка сервера');
                }

                const data = await response.json();

                // Удаляем временную панель
                tempPanel.remove();

                // Создаем постоянную панель с данными от сервера
                const panel = document.createElement('div');
                panel.className = 'panel';

                const iconWrapper = document.createElement('div');
                iconWrapper.className = 'icon-wrapper';
                const icon = document.createElement('img');
                icon.src = `/static/icon/${data.icon || iconNumber}.png`;
                iconWrapper.appendChild(icon);

                const left = document.createElement('div');
                left.style.display = 'flex';
                left.style.alignItems = 'center';

                const nameSpan = document.createElement('span');
                nameSpan.textContent = name;

                left.appendChild(iconWrapper);
                left.appendChild(nameSpan);

                const project_index = document.createElement('span');
                project_index.className = 'panel-number';
                project_index.textContent = container.children.length + 1;

                const close = document.createElement('span');
                close.innerHTML = '&times;';
                close.className = 'close-btn';

                panel.appendChild(left);
                panel.appendChild(project_index);
                panel.appendChild(close);
                container.appendChild(panel);

                // Обновляем нумерацию
                updateProjectIndices();

                // Обработчик удаления для новой панели
                close.onclick = (e) => {
                    e.stopPropagation();
                    fetch(`/api/projects/${data.id}`, {
                        method: 'DELETE'
                    }).then(() => {
                        panel.remove();
                        updateProjectIndices();
                    }).catch(err => {
                        console.error('Ошибка при удалении:', err);
                    });
                };

            } catch (err) {
                console.error('Ошибка при добавлении проекта:', err);
                alert('Не удалось добавить проект');
            }
        }
    });
});