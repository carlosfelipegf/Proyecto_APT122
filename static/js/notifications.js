$(document).ready(function() {
    // Función principal para obtener y mostrar notificaciones
    function fetchNotifications() {
        $.ajax({
            // RUTA CORREGIDA: Añadido /usuarios/
            url: '/usuarios/api/notifications/get/',
            method: 'GET',
            success: function(response) {
                const list = $('#notification-list');
                const countSpan = $('#notification-count');
                const notifications = response.notifications;
                const unreadCount = response.unread_count;
                
                // 1. Limpiar lista anterior (excepto el separador y la opción de marcar todo)
                // Usamos :not(.static-item) si las últimas dos opciones tienen esa clase, 
                // si no, el selector original es correcto si el loading y el no-notifications son los únicos que quedan al final.
                list.find('.notification-item-generated').remove(); // Remover solo las generadas

                // 2. Actualizar contador
                if (unreadCount > 0) {
                    countSpan.text(unreadCount).show();
                } else {
                    countSpan.hide().text('0');
                }

                // 3. Mostrar o generar notificaciones
                if (notifications.length === 0) {
                    $('#no-notifications-item').show();
                    $('#loading-item').hide();
                } else {
                    $('#no-notifications-item').hide();
                    $('#loading-item').hide();

                    notifications.forEach(n => {
                        // Class para marcar solo las generadas y poder borrarlas después
                        const isReadClass = n.is_read ? '' : 'fw-bold'; 
                        
                        const listItem = $(
                            `<li class="notification-item-generated" data-id="${n.id}">
                                <a class="dropdown-item notification-item ${isReadClass}" href="${n.link}">
                                    <small class="d-block text-muted">${n.timestamp}</small>
                                    ${n.message}
                                </a>
                            </li>`
                        );
                        // Insertar la nueva notificación antes del divisor (asumiendo que es el último elemento importante)
                        list.find('.dropdown-divider').before(listItem);
                    });
                }
            },
            error: function(xhr, status, error) {
                // console.error("Error al cargar notificaciones:", error);
                $('#loading-item').hide();
                $('#no-notifications-item').text('Error al cargar.');
            }
        });
    }

    // Al hacer clic en el ítem, marca la notificación como leída
    $('#notification-list').on('click', '.notification-item', function(e) {
        const notificationId = $(this).closest('li').data('id');
        
        // Evita que el enlace abra la página inmediatamente
        e.preventDefault(); 
        
        $.ajax({
            // RUTA CORREGIDA: Añadido /usuarios/
            url: '/usuarios/api/notifications/read/',
            method: 'POST',
            data: JSON.stringify({ ids: [notificationId] }),
            contentType: 'application/json',
            headers: {
                // Obtener el token CSRF para peticiones POST en Django
                'X-CSRFToken': $('[name="csrfmiddlewaretoken"]').val() || getCookie('csrftoken')
            },
            success: function() {
                // Redirigir después de marcar como leída
                window.location.href = $(e.currentTarget).attr('href');
            },
            error: function(xhr, status, error) {
                // Si falla la API, redirige de todos modos
                console.error("Error al marcar como leído:", error);
                window.location.href = $(e.currentTarget).attr('href');
            }
        });
    });

    // Función para obtener cookie CSRF (necesario si no está en el formulario)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Marcar todas como leídas (al hacer clic en el botón del dropdown)
    window.markAllAsRead = function(event) {
        event.preventDefault(); 
        $.ajax({
            // RUTA CORREGIDA: Añadido /usuarios/
            url: '/usuarios/api/notifications/read/',
            method: 'POST',
            data: JSON.stringify({ mark_all: true }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': $('[name="csrfmiddlewaretoken"]').val() || getCookie('csrftoken')
            },
            success: function() {
                // Vuelve a cargar el estado de las notificaciones para actualizar el contador y la lista
                fetchNotifications();
            },
            error: function() {
                alert('No se pudieron marcar todas las notificaciones como leídas. Por favor, revise la consola.');
            }
        });
    }
    

    // Iniciar la carga de notificaciones al cargar la página
    fetchNotifications();

    // Opcional: Recargar notificaciones cada 60 segundos (Polling)
    // setInterval(fetchNotifications, 60000); 
});