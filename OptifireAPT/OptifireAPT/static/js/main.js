document.addEventListener("DOMContentLoaded", function() {
    
    // --- 1. CONTROL DEL LOADER GLOBAL ---
    const loader = document.getElementById('global-loader');

    window.showLoader = function() {
        if(loader) loader.classList.remove('d-none');
    };

    window.hideLoader = function() {
        if(loader) loader.classList.add('d-none');
    }

    if (loader) {
        // Cerrar al hacer click fuera
        loader.addEventListener('click', function(e) {
            if(e.target === loader) hideLoader();
        });

        // SEGURIDAD: Si hay errores visibles, ocultar loader para que el usuario los vea
        const errorAlerts = document.querySelectorAll('.alert-danger, .alert-warning, .errorlist');
        if (errorAlerts.length > 0) {
            hideLoader();
        }

        // Restaurar estado al volver atrás (bfcache)
        window.addEventListener('pageshow', function(event) {
            hideLoader();
        });
    }

    // --- 2. INTERCEPTOR DE FORMULARIOS ---
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Esperar validación nativa del navegador
            setTimeout(() => {
                if (!e.defaultPrevented && form.checkValidity()) {
                    showLoader();
                }
            }, 50);
        });
    });

});

// --- 3. FUNCIÓN PARA MARCAR NOTIFICACIONES COMO LEÍDAS (AJAX) ---
// Esta función se llama desde los botones de las notificaciones
function marcarLeido(id) {
    if (!id) return;
    
    fetch(`/usuarios/notificacion/leida/${id}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if(response.ok) {
            console.log("Notificación marcada como leída: " + id);
            // Opcional: Podrías remover el elemento del DOM aquí si quisieras
        }
    })
    .catch(error => console.error('Error al marcar notificación:', error));
}