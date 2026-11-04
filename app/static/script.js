
const form = document.getElementById("profileForm");
const resultado = document.getElementById("resultado");
const boton = document.getElementById("btnAnalizar");

let datosDashboard = null;
let compatibilidadChart = null;
let transicionesChart = null;
let mercadoChart = null;


// Cargar los datos de las gráficas desde Flask
async function cargarDashboard() {
    const estado = document.getElementById("estadoDashboard");

    try {
        estado.textContent = "Cargando datos...";

        const response = await fetch("/api/dashboard-data");

        if (!response.ok) {
            throw new Error("No fue posible obtener los datos.");
        }

        datosDashboard = await response.json();

        cargarPerfiles();
        dibujarTransiciones();
        dibujarMercado();

        estado.textContent = "Gráficas cargadas correctamente.";

    } catch (error) {
        estado.textContent = "No fue posible cargar las gráficas.";
        console.error(error);
    }
}


// Cargar los perfiles de demostración
function cargarPerfiles() {
    const selector = document.getElementById("perfilDemo");

    selector.replaceChildren();

    datosDashboard.perfiles.perfiles.forEach((perfil, indice) => {
        const opcion = document.createElement("option");

        opcion.value = indice;
        opcion.textContent = perfil.perfil;

        selector.appendChild(opcion);
    });

    selector.addEventListener("change", dibujarCompatibilidad);

    dibujarCompatibilidad();
}


// Primera gráfica: compatibilidad profesional
function dibujarCompatibilidad() {
    const indice = Number(document.getElementById("perfilDemo").value);
    const perfil = datosDashboard.perfiles.perfiles[indice];

    if (!perfil) return;

    const familias = perfil.top_familias.slice(0, 8);

    const contexto = document
        .getElementById("compatibilidadChart")
        .getContext("2d");

    if (compatibilidadChart) {
        compatibilidadChart.destroy();
    }

    compatibilidadChart = new Chart(contexto, {
        type: "bar",
        data: {
            labels: familias.map(item => item.familia),
            datasets: [{
                label: "Compatibilidad (%)",
                data: familias.map(item => item.cobertura_pct),
                backgroundColor: "#3b82f6",
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: "Compatibilidad (%)"
                    }
                }
            }
        }
    });

    // Mostrar habilidades presentes y faltantes
    const detalle = document.getElementById("detalleHabilidades");
    detalle.replaceChildren();

    const titulo = document.createElement("h4");
    titulo.textContent = "Detalle de habilidades";
    detalle.appendChild(titulo);

    const presentes = document.createElement("p");
    presentes.textContent =
        "Habilidades presentes: " +
        (familias[0]?.presentes.join(", ") || "No disponibles");

    const faltantes = document.createElement("p");
    faltantes.textContent =
        "Habilidades por aprender: " +
        (familias[0]?.faltantes_principales.join(", ") || "No disponibles");

    detalle.append(presentes, faltantes);
}


// Segunda gráfica: transiciones profesionales
function dibujarTransiciones() {
    const transiciones = [...datosDashboard.transiciones.transiciones]
        .sort((a, b) => b.similitud - a.similitud)
        .slice(0, 10);

    const contexto = document
        .getElementById("transicionesChart")
        .getContext("2d");

    transicionesChart = new Chart(contexto, {
        type: "bar",
        data: {
            labels: transiciones.map(
                item => `${item.origen} → ${item.destino}`
            ),
            datasets: [{
                label: "Similitud (%)",
                data: transiciones.map(item => item.similitud * 100),
                backgroundColor: "#8b5cf6",
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: "Similitud (%)"
                    }
                }
            }
        }
    });
}


// Tercera gráfica: mercado laboral
function dibujarMercado() {
    const ofertas = datosDashboard.mercado.ofertas_por_familia
        .slice()
        .sort((a, b) => b.ofertas - a.ofertas)
        .slice(0, 10);

    const contexto = document
        .getElementById("mercadoChart")
        .getContext("2d");

    mercadoChart = new Chart(contexto, {
        type: "bar",
        data: {
            labels: ofertas.map(item => item.familia),
            datasets: [{
                label: "Número de ofertas",
                data: ofertas.map(item => item.ofertas),
                backgroundColor: "#10b981",
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Ofertas laborales"
                    }
                }
            }
        }
    });

    // Mostrar habilidades más solicitadas
    const lista = document.getElementById("habilidadesMercado");
    lista.replaceChildren();

    datosDashboard.mercado.habilidades_mas_pedidas
        .slice(0, 10)
        .forEach(habilidad => {
            const elemento = document.createElement("li");

            elemento.textContent =
                `${habilidad.habilidad} - ${habilidad.porcentaje}%`;

            lista.appendChild(elemento);
        });
}


// Enviar formulario a Flask
form.addEventListener("submit", async function(event) {
    event.preventDefault();

    const nombre = document.getElementById("nombre").value.trim();
    const perfil = document.getElementById("perfil").value.trim();
    const habilidades = document.getElementById("habilidades").value.trim();
    const objetivo = document.getElementById("objetivo").value;

    if (!nombre || !perfil || !habilidades || !objetivo) {
        resultado.hidden = false;
        resultado.textContent = "Completa todos los campos para continuar.";
        return;
    }

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
            mensaje.textContent = data.message;
        } else if (response.ok) {
            mensaje.textContent =
                data.message || "Tu perfil fue procesado correctamente.";
        } else {
            mensaje.textContent =
                data.error || "No fue posible procesar tu perfil.";
        }

        resultado.append(titulo, mensaje);

    } catch (error) {
        resultado.textContent =
            "No se pudo conectar con el servidor.";

        console.error("Error:", error);

    } finally {
        boton.disabled = false;
    }
});


// Iniciar las gráficas cuando se carga la página
cargarDashboard();
