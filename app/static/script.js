
const form = document.getElementById("profileForm");
const resultado = document.getElementById("resultado");

form.addEventListener("submit", function (event) {
    event.preventDefault();

    const nombre = document.getElementById("nombre").value.trim();
    const perfil = document.getElementById("perfil").value.trim();
    const habilidades = document.getElementById("habilidades").value.trim();
    const objetivo = document.getElementById("objetivo").value;

    if (!nombre || !perfil || !habilidades || !objetivo) {
        resultado.hidden = false;
        resultado.textContent =
            "Completa todos los campos para continuar.";
        return;
    }

    resultado.hidden = false;
    resultado.replaceChildren();

    const titulo = document.createElement("h3");
    titulo.textContent = `¡Gracias, ${nombre}!`;

    const mensaje = document.createElement("p");
    mensaje.textContent =
        `Tu perfil de ${perfil} se ha capturado correctamente. ` +
        `Tu objetivo es ${objetivo}. El siguiente paso será conectar ` +
        `este formulario con el motor de análisis de CareerTwin AI.`;

    resultado.append(titulo, mensaje);
});
