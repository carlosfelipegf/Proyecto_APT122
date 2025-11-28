document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector("form");
    
    if (!form) return;

    form.addEventListener("submit", function (event) {
        let errores = [];
        
        // Obtenemos los campos por los IDs que genera Django Crispy Forms
        const nombre = document.getElementById("id_first_name");
        const email = document.getElementById("id_email");
        const password = document.getElementById("id_password");
        const confirmarPassword = document.getElementById("id_confirmar_password"); // Asegúrate que este ID coincida
        const rut = document.getElementById("id_rut");

        // Limpiar alertas previas
        document.querySelectorAll(".alert-js-error").forEach(el => el.remove());

        // 1. Validar Nombre
        if (nombre && nombre.value.trim().length < 3) {
            errores.push("El nombre debe tener al menos 3 caracteres.");
            marcarError(nombre);
        }

        // 2. Validar Email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (email && !emailRegex.test(email.value.trim())) {
            errores.push("El correo electrónico no es válido.");
            marcarError(email);
        }

        // 3. Validar Contraseña Fuerte
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
        if (password && !passwordRegex.test(password.value)) {
            errores.push("La contraseña debe tener: 8+ caracteres, 1 mayúscula, 1 minúscula y 1 número.");
            marcarError(password);
        }

        // 4. Confirmar Contraseña
        if (password && confirmarPassword && password.value !== confirmarPassword.value) {
            errores.push("Las contraseñas no coinciden.");
            marcarError(confirmarPassword);
        }

        // 5. Validar RUT
        if (rut && !validarRut(rut.value.trim())) {
            errores.push("El RUT ingresado no es válido.");
            marcarError(rut);
        }

        // Si hay errores, prevenimos el envío y mostramos alerta
        if (errores.length > 0) {
            event.preventDefault(); // DETIENE EL ENVÍO A DJANGO
            mostrarErroresArriba(errores);
        }
    });
});

function marcarError(input) {
    input.classList.add("is-invalid");
    input.addEventListener("input", () => input.classList.remove("is-invalid"));
}

function mostrarErroresArriba(listaErrores) {
    const contenedor = document.querySelector(".card-body");
    const divError = document.createElement("div");
    divError.className = "alert alert-danger alert-dismissible fade show alert-js-error shadow-sm";
    divError.innerHTML = `
        <strong><i class="fas fa-exclamation-triangle me-2"></i>Por favor corrige lo siguiente:</strong>
        <ul class="mb-0 mt-2">
            ${listaErrores.map(e => `<li>${e}</li>`).join('')}
        </ul>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    contenedor.prepend(divError);
    window.scrollTo(0, 0); // Subir para ver el error
}

// Algoritmo de RUT Chileno
function validarRut(rutCompleto) {
    if (!rutCompleto) return true; // Si es opcional, dejar pasar vacío (o false si es obligatorio)
    rutCompleto = rutCompleto.replace(/\./g, "").replace("-", "").toUpperCase();
    
    if (rutCompleto.length < 8) return false;

    const cuerpo = rutCompleto.slice(0, -1);
    const dv = rutCompleto.slice(-1);
    let suma = 0;
    let multiplo = 2;

    for (let i = cuerpo.length - 1; i >= 0; i--) {
        suma += parseInt(cuerpo[i]) * multiplo;
        multiplo = multiplo === 7 ? 2 : multiplo + 1;
    }

    let dvEsperado = 11 - (suma % 11);
    dvEsperado = dvEsperado === 11 ? "0" : dvEsperado === 10 ? "K" : dvEsperado.toString();

    return dv === dvEsperado;
}