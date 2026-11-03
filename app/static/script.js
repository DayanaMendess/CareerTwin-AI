
const form = document.getElementById("profileForm");
const resultado = document.getElementById("resultado");
const boton = document.getElementById("btnAnalizar");

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const nombre = document.getElementById("nombre").value.trim();
    const perfil = document.getElementById("perfil").value.trim();
    const habilidades = document.getElementById("habilidades").value.trim();
    const objetivo = document.getElementById("objetivo").value;

    // Validar los campos
    if (!nombre || !perfil || !habilidades || !objetivo) {
        resultado.hidden = false;
        resultado.textContent = "Completa todos los campos para continuar.";
        return;
    }

    // Preparar la información
    const profileText = `
        Nombre: ${nombre}
        Perfil profesional: ${perfil}
        Habilidades: ${habilidades}
        Objetivo laboral: ${objetivo}
    `;

    resultado.hidden = false;
    resultado.textContent = "Enviando información al servidor...";
    boton.disabled = true;

    try {
        // Enviar información a Flask
        const response = await fetch("/api/analyze-profile", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                profile_text: profileText
            })
        });

        const data = await response.json();

        resultado.replaceChildren();

        const titulo = document.createElement("h3");
        titulo.textContent = `¡Gracias, ${nombre}!`;

        const mensaje = document.createElement("p");

        if (response.status === 503) {
            mensaje.textContent =
                data.message ||
                "Tu perfil fue recibido correctamente. El modelo de inteligencia artificial todavía no está disponible.";
        } else if (response.ok) {
            mensaje.textContent =
                data.message || "Tu perfil fue procesado correctamente.";
        } else {
            mensaje.textContent =
                data.error || "No fue posible procesar tu perfil.";
        }

        resultado.append(titulo, mensaje);

    } catch (error) {
        resultado.hidden = false;
        resultado.textContent =
            "No se pudo conectar con el servidor. Verifica que Flask esté funcionando.";

        console.error("Error:", error);

    } finally {
        boton.disabled = false;
    }
});
