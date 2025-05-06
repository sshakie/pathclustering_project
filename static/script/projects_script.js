const container = document.getElementById('projects');

data.forEach((project, index) => {
    const panel = document.createElement('div');
    panel.className = 'panel';
    panel.dataset.projectId = project.id;

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

container.addEventListener('click', (e) => {
    const panel = e.target.closest('.panel');
    if (!panel) return;

    if (e.target.classList.contains('close-btn')) return;

    const projectId = panel.dataset.projectId;
    if (projectId) {
        window.location.href = `/projects/${projectId}`;
    }
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

function isProjectNameExists(name) {
    const projects = document.querySelectorAll('.panel:not(.temp-panel)');
    for (const project of projects) {
        const projectName = project.querySelector('span:not(.panel-number):not(.close-btn)');
        if (projectName && projectName.textContent.toLowerCase() === name.toLowerCase()) {
            return true;
        }
    }
    return false;
}

document.getElementById('add-project-btn').addEventListener('click', () => {
    const tempPanel = document.createElement('div');
    tempPanel.className = 'panel temp-panel';

    const iconNumber = Math.floor(Math.random() * 4) + 1;
    const iconWrapper = document.createElement('div');
    iconWrapper.className = 'icon-wrapper';
    const icon = document.createElement('img');
    icon.src = `/static/icon/${iconNumber}.png`;
    iconWrapper.appendChild(icon);

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Введите название';
    input.style.fontSize = '20px';
    input.style.border = 'none';
    input.style.outline = 'none';
    input.style.background = 'transparent';

    const left = document.createElement('div');
    left.style.display = 'flex';
    left.style.alignItems = 'center';
    left.appendChild(iconWrapper);
    left.appendChild(input);

    const projectIndex = document.createElement('span');
    projectIndex.className = 'panel-number';
    projectIndex.textContent = container.children.length + 1;
    projectIndex.style.marginLeft = '-20px';

    const close = document.createElement('span');
    close.innerHTML = '&times;';
    close.className = 'close-btn';
    close.onclick = (e) => {
        e.stopPropagation();
        tempPanel.remove();
    };

    tempPanel.appendChild(left);
    tempPanel.appendChild(projectIndex);
    tempPanel.appendChild(close);
    container.appendChild(tempPanel);

    input.focus();

    input.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            const name = input.value.trim();
            if (!name) return;

            if (isProjectNameExists(name)) {
            input.classList.add('flash-duplicate');

            setTimeout(() => {
                input.classList.remove('flash-duplicate');
            }, 800);

            return;
        }

            try {
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

                tempPanel.remove();

                const panel = document.createElement('div');
                panel.className = 'panel';
                panel.dataset.projectId = data.id;

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

                updateProjectIndices();

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