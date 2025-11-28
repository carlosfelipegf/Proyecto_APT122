/**
 * Lógica para captura de evidencia fotográfica en inspecciones.
 * Maneja la cámara web, el canvas y la transferencia de archivos al input.
 */

let currentInputId = null;       // ID del input type="file" que recibirá la foto
let currentPreviewPrefix = null; // Prefijo para actualizar la UI de esa tarea
let videoStream = null;          // Flujo de video de la cámara

// 1. ABRIR CÁMARA (Inicia el modal y el stream)
async function abrirCamara(inputId, previewPrefix) {
    currentInputId = inputId;
    currentPreviewPrefix = previewPrefix;
    
    const modalElement = document.getElementById('cameraModal');
    const modal = new bootstrap.Modal(modalElement);
    const video = document.getElementById('videoElement');

    try {
        // Solicitamos acceso a la cámara (preferencia: trasera/environment)
        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: "environment", 
                width: { ideal: 1280 }, 
                height: { ideal: 720 } 
            } 
        });
        video.srcObject = videoStream;
        modal.show();
    } catch (err) {
        console.error("Error de cámara:", err);
        alert("No se pudo acceder a la cámara. Verifique los permisos o use la opción de subir archivo.\nError: " + err.message);
    }
}

// 2. TOMAR FOTO (Captura el frame y lo convierte a archivo)
function tomarFoto() {
    const video = document.getElementById('videoElement');
    const canvas = document.getElementById('canvasElement');
    
    // Si el video no está listo, salimos
    if (video.readyState !== 4) return;

    // Configurar canvas al tamaño real del video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Dibujar
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convertir a Blob -> File -> Input
    canvas.toBlob(blob => {
        // Creamos un nombre de archivo único con timestamp
        const fileName = "evidencia_cam_t" + Date.now() + ".jpg";
        const file = new File([blob], fileName, { type: "image/jpeg" });
        
        // Usamos DataTransfer para simular una selección de archivo nativa
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        
        // Asignamos el archivo al input oculto de Django
        const input = document.getElementById(currentInputId);
        input.files = dataTransfer.files;

        // Actualizamos la vista previa visualmente
        mostrarPreview(canvas.toDataURL("image/jpeg"));

        // Cerramos todo
        detenerCamara();
        const modalElement = document.getElementById('cameraModal');
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        modalInstance.hide();

    }, 'image/jpeg', 0.8); // Calidad JPG 80%
}

// 3. MOSTRAR PREVIEW (Actualiza la UI de la tarjeta específica)
function mostrarPreview(imageDataUrl) {
    const container = document.getElementById(currentPreviewPrefix + '-container');
    const img = document.getElementById(currentPreviewPrefix + '-img');
    const text = document.getElementById(currentPreviewPrefix + '-text');

    img.src = imageDataUrl;
    container.classList.remove('d-none');
    
    text.innerText = "Imagen capturada lista para guardar.";
    text.classList.remove('text-muted', 'fst-italic');
    text.classList.add('text-success', 'fw-bold');
}

// 4. DETENER CÁMARA (Libera el hardware)
function detenerCamara() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
}

// 5. BORRAR FOTO (Limpia el input y la UI)
function borrarFoto(inputId, previewPrefix) {
    const input = document.getElementById(inputId);
    input.value = ""; // Vacia el input de archivo
    
    const container = document.getElementById(previewPrefix + '-container');
    container.classList.add('d-none'); // Oculta la foto
    
    const text = document.getElementById(previewPrefix + '-text');
    text.innerText = "Captura eliminada.";
    text.classList.remove('text-success', 'fw-bold');
    text.classList.add('text-danger');
    
    // Restaurar texto original después de 2 segundos (opcional estético)
    setTimeout(() => {
        text.innerText = "Sin evidencia nueva.";
        text.classList.remove('text-danger');
        text.classList.add('text-muted');
    }, 2000);
}