const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const form = document.getElementById('uploadForm');
const loadingBox = document.getElementById('loadingBox');
const progressBar = document.getElementById('progressBar');
const statusText = document.getElementById('statusText');
const submitBtn = document.getElementById('submitBtn');

function closeModal() {
    modal.style.display = 'none';
    photoInput.value = ""; 
};

let currentFiles = [];

if (dropZone) {
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
        currentFiles = [...currentFiles, ...e.dataTransfer.files];
        updateFileInput();
        showFiles();
    });
}

if (fileInput) {
    fileInput.addEventListener('change', () => {
        currentFiles = [...currentFiles, ...fileInput.files];
        showFiles();
    });
}

function updateFileInput() {
    const dataTransfer = new DataTransfer();
    currentFiles.forEach(file => {
        dataTransfer.items.add(file);
    });
    fileInput.files = dataTransfer.files;
}

function showFiles() {
    if (!fileList) return;
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

function moveUp(index) {
    if (index === 0) return;
    [currentFiles[index], currentFiles[index - 1]] = [currentFiles[index - 1], currentFiles[index]];
    showFiles();
}

function moveDown(index) {
    if (index === currentFiles.length - 1) return;
    [currentFiles[index], currentFiles[index + 1]] = [currentFiles[index + 1], currentFiles[index]];
    showFiles();
}

function removeFile(index) {
    currentFiles.splice(index, 1);
    showFiles();
}

if (form) {
    form.addEventListener('submit', (e) => {
        if (currentFiles.length === 0) {
            e.preventDefault();
            alert('Selecione pelo menos um arquivo.');
            return;
        }

        e.preventDefault();
        
        // Esconde o botão e mostra o loading
        submitBtn.style.display = 'none';
        loadingBox.style.display = 'flex';
        
        const formData = new FormData(form);
        const xhr = new XMLHttpRequest();

        // Progresso do Upload
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 50); // Upload é 50% do processo
                updateProgress(percent, 'Enviando arquivo...');
            }
        });

        xhr.onreadystatechange = function() {
            if (xhr.readyState === 3) { // Processando no servidor
                updateProgress(75, 'Processando conversão...');
            }
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    updateProgress(100, 'Concluído! Baixando...');
                    
                    // Simula o download do arquivo recebido
                    const blob = new Blob([xhr.response], { type: xhr.getResponseHeader('Content-Type') });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    
                    // Tenta pegar o nome do arquivo do header
                    const contentDisposition = xhr.getResponseHeader('Content-Disposition');
                    let fileName = 'convertido.file';
                    if (contentDisposition && contentDisposition.indexOf('filename=') !== -1) {
                        fileName = contentDisposition.split('filename=')[1].replace(/"/g, '');
                    } else {
                        // Fallback baseado na rota
                        if (form.action.includes('word')) fileName = 'documento.docx';
                        else if (form.action.includes('excel')) fileName = 'planilha.xlsx';
                        else if (form.action.includes('pdf')) fileName = 'arquivo.pdf';
                    }

                    a.href = url;
                    a.download = fileName;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    // Reset do form após sucesso
                    setTimeout(() => {
                        loadingBox.style.display = 'none';
                        submitBtn.style.display = 'block';
                        updateProgress(0, '');
                    }, 2000);
                } else {
                    alert('Erro na conversão. Tente novamente.');
                    loadingBox.style.display = 'none';
                    submitBtn.style.display = 'block';
                }
            }
        };

        xhr.open('POST', form.action, true);
        xhr.responseType = 'blob';
        xhr.send(formData);
    });
}

function updateProgress(percent, text) {
    if (progressBar) progressBar.style.width = percent + '%';
    if (statusText) statusText.innerText = text;
}
