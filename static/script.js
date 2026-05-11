const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const form = document.getElementById('uploadForm');

let currentFiles = [];

dropZone.addEventListener('click', () => {
    fileInput.click();
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {

    e.preventDefault();

    dropZone.classList.remove('dragover');

    currentFiles = [
        ...currentFiles,
        ...e.dataTransfer.files
    ];

    updateFileInput();

    showFiles();
});

fileInput.addEventListener('change', () => {

    currentFiles = [
        ...currentFiles,
        ...fileInput.files
    ];

    showFiles();
});

function updateFileInput(){

    const dataTransfer = new DataTransfer();

    currentFiles.forEach(file => {
        dataTransfer.items.add(file);
    });

    fileInput.files = dataTransfer.files;
}

function showFiles(){

    fileList.innerHTML = '';

    currentFiles.forEach((file, index) => {

        const div = document.createElement('div');

        div.classList.add('file-item');

        div.innerHTML = `
            <span>${file.name}</span>

            <div class="actions">

                <button type="button" onclick="moveUp(${index})">↑</button>

                <button type="button" onclick="moveDown(${index})">↓</button>

                <button type="button" onclick="removeFile(${index})">✕</button>

            </div>
        `;

        fileList.appendChild(div);
    });

    updateFileInput();
}

function moveUp(index){

    if(index === 0) return;

    [currentFiles[index], currentFiles[index - 1]] =
    [currentFiles[index - 1], currentFiles[index]];

    showFiles();
}

function moveDown(index){

    if(index === currentFiles.length - 1) return;

    [currentFiles[index], currentFiles[index + 1]] =
    [currentFiles[index + 1], currentFiles[index]];

    showFiles();
}

function removeFile(index){

    currentFiles.splice(index, 1);

    showFiles();
}

form.addEventListener('submit', (e) => {

    if(currentFiles.length === 0){

        e.preventDefault();

        alert('Selecione pelo menos um PDF.');
    }
});