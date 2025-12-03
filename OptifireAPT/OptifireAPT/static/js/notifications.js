/**
 * notifications.js
 * Maneja la lógica de las notificaciones tipo Toast y su marcado como leídas.
 */

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
            
            // Opcional: Si quieres que el toast desaparezca visualmente al hacer clic en el botón de acción
            // const toastElement = document.getElementById('toast-' + id);
            // if (toastElement) {
            //     const bsToast = bootstrap.Toast.getInstance(toastElement);
            //     if (bsToast) bsToast.hide();
            // }
        }
    })
    .catch(error => console.error('Error al marcar notificación:', error));
}

// Inicialización de Toasts (si Bootstrap lo requiere explícitamente)
document.addEventListener("DOMContentLoaded", function() {
    var toastElList = [].slice.call(document.querySelectorAll('.toast'));
    var toastList = toastElList.map(function(toastEl) {
        return new bootstrap.Toast(toastEl, { autohide: false });
    });
});