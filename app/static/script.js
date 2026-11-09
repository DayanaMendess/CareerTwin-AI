
const form = document.getElementById("profileForm");
const resultado = document.getElementById("resultado");
const boton = document.getElementById("btnAnalizar");

let datosDashboard = null;
let compatibilidadChart = null;
let transicionesChart = null;
let mercadoChart = null;


// ==========================================
// FUNCIONES GENERALES
// ==========================================


function obtenerLista(valor) {
    return Array.isArray(valor) ? valor : [];
}

function mostrarEstado(tipo, mensaje) {
    const seccion = document.getElementById("resultadosUsuario");
    const estado = document.getElementById("estadoAnalisis");

    seccion.hidden = false;
    estado.className = `analysis-status ${tipo}`;
    estado.textContent = mensaje;
}

function mostrarHabilidades(elementoId, habilidades, clase, mensajeVacio = "No hay habilidades disponibles.") {
    const contenedor = document.getElementById(elementoId);
    contenedor.replaceChildren();

    const lista = obtenerLista(habilidades);

    if (lista.length === 0) {
        const mensaje = document.createElement("span");
        mensaje.className = "empty-message";
        mensaje.textContent = mensajeVacio;
        contenedor.appendChild(mensaje);
        return;
    }

    lista.forEach(item => {
        const habilidadOriginal = typeof item === "string" ? item : item.habilidad;
        const traducciones = {
            "communication": "comunicaci\u00f3n",
            "teamwork": "trabajo en equipo",
            "problem solving": "resoluci\u00f3n de problemas",
            "troubleshooting": "soluci\u00f3n de problemas t\u00e9cnicos",
            "customer service": "atenci\u00f3n al cliente",
            "critical thinking": "pensamiento cr\u00edtico",
            "electrical engineering": "ingenier\u00eda el\u00e9ctrica",
            "mechanical engineering": "ingenier\u00eda mec\u00e1nica",
            "civil engineering": "ingenier\u00eda civil",
            "project management": "gesti\u00f3n de proyectos",
            "microsoft office": "Microsoft Office",
            "organizational skills": "organizaci\u00f3n",
            "adaptability": "adaptabilidad",
            "time management": "gesti\u00f3n del tiempo",
            "software development": "desarrollo de software",
            "quality control": "control de calidad",
            "attention to detail": "atenci\u00f3n al detalle",
            "agile": "metodolog\u00edas \u00e1giles",
            "maintenance": "mantenimiento",
            "computer science": "ciencias de la computaci\u00f3n",
            "java": "Java",
            "aws": "AWS"
        };
        const habilidad = traducciones[String(habilidadOriginal).toLowerCase()] || habilidadOriginal;

        if (!habilidad) return;

        const tarjeta = document.createElement("div");
        tarjeta.className = "skill-card";

        const etiqueta = document.createElement("strong");
        etiqueta.className = `skill-tag ${clase}`;
        etiqueta.textContent = habilidad;
        tarjeta.appendChild(etiqueta);

        if (typeof item === "object") {
            if (item.categoria) {
                const detalle = document.createElement("small");
                detalle.textContent = `Categoría: ${({ tecnica: "T\u00e9cnica", blanda: "Blanda" })[String(item.categoria).toLowerCase()] || item.categoria}`;
                tarjeta.appendChild(detalle);
            }

            if (item.probabilidad !== null && item.probabilidad !== undefined) {
                let puntuacion = Number(item.probabilidad);

                if (Number.isFinite(puntuacion)) {
                    if (puntuacion >= 0 && puntuacion <= 1) {
                        puntuacion *= 100;
                    }

                    const detalle = document.createElement("small");
                    detalle.textContent = `Puntuación del modelo: ${puntuacion.toFixed(1)}%`;
                    tarjeta.appendChild(detalle);
                }
            }

            if (item.evidencia) {
                const evidencia = document.createElement("small");
                const textoEvidencia = String(item.evidencia);
                const evidenciaTraducida = textoEvidencia
                    .replace(/Fortalecer time management/gi, "Fortalecer gesti\u00f3n del tiempo")
                    .replace(/Fortalecer software development/gi, "Fortalecer desarrollo de software")
                    .replace(/Fortalecer quality control/gi, "Fortalecer control de calidad")
                    .replace(/Fortalecer attention to detail/gi, "Fortalecer atenci?n al detalle")
                    .replace(/Fortalecer maintenance/gi, "Fortalecer mantenimiento")
                    .replace(/es una habilidad solicitada en estas familias:/gi, "es una habilidad solicitada en estas familias:");
                evidencia.textContent = `Evidencia: ${evidenciaTraducida}`;
                tarjeta.appendChild(evidencia);
            }
        }

        contenedor.appendChild(tarjeta);
    });
}
function mostrarResultadosUsuario(data) {
    const detectadas = obtenerLista(data.habilidades_detectadas);

    const texto = detectadas.filter(item => item.fuente === "texto");
    const modelo = detectadas.filter(item => item.fuente === "modelo");
    const ambas = detectadas.filter(item => item.fuente === "texto+modelo");

    mostrarHabilidades("habilidadesTexto", texto, "skill-text");
    mostrarHabilidades("habilidadesModelo", modelo, "skill-model");
    mostrarHabilidades("habilidadesAmbos", ambas, "skill-both");

    mostrarHabilidades(
        "habilidadesPresentes",
        detectadas,
        "skill-present",
        "No se identificaron habilidades."
    );

    const brechas = obtenerLista(data.brechas_habilidades).map(item => ({
        ...item,
        evidencia: `Prioridad en la familia laboral: ${item.pct_en_familia ?? 0}%`
    }));

    mostrarHabilidades(
        "brechasHabilidades",
        brechas,
        "skill-gap",
        "No se identificaron brechas."
    );

    const familiasCalculadas = obtenerLista(data.mejores_familias);
    const compatibilidad = Number(
        familiasCalculadas.length
            ? familiasCalculadas[0].compatibilidad
            : data.compatibilidad
    );
    const porcentaje = Number.isFinite(compatibilidad)
        ? Math.max(0, Math.min(100, compatibilidad))
        : 0;

    document.getElementById("compatibilidadValor").textContent =
        `${porcentaje.toFixed(1)}%`;

    document.getElementById("compatibilidadNivel").textContent =
        data.familia_recomendada
            ? `Familia con mayor coincidencia: ${data.familia_recomendada}`
            : "No se pudo determinar una familia laboral.";

    document.getElementById("compatibilidadBarra").style.width =
        `${porcentaje}%`;

    const contenedorFamilias = document.getElementById("mejoresFamilias");
    contenedorFamilias.replaceChildren();

    obtenerLista(data.mejores_familias).forEach((familia, indice) => {
        const tarjeta = document.createElement("div");
        tarjeta.className = "skill-card";

        const titulo = document.createElement("strong");
        titulo.textContent = `${indice + 1}. ${familia.familia}`;

        const detalle = document.createElement("p");
        detalle.textContent =
            `${familia.compatibilidad}% de coincidencia ` +
            `(${familia.habilidades_coincidentes} de ${familia.habilidades_requeridas} habilidades)`;

        tarjeta.append(titulo, detalle);
        contenedorFamilias.appendChild(tarjeta);
    });

    if (!contenedorFamilias.children.length) {
        contenedorFamilias.textContent = "No hay familias laborales disponibles.";
    }

    const recomendaciones = obtenerLista(data.recomendaciones).map(item => ({
        ...item,
        evidencia: item.mensaje || ""
    }));

    mostrarHabilidades(
        "recomendaciones",
        recomendaciones,
        "recommendation",
        "No hay recomendaciones disponibles."
    );

    document.querySelectorAll(".analysis-warning").forEach(item => item.remove());

    if (data.advertencia) {
        const advertencia = document.createElement("p");
        advertencia.className = "analysis-warning";
        advertencia.textContent = data.advertencia;
        document.getElementById("resultadosUsuario").appendChild(advertencia);
    }

    mostrarEstado(
        "success",
        `Análisis completado. Se identificaron ${detectadas.length} habilidades.`
    );
}


// MANEJO DE ERRORES Y MODELO NO DISPONIBLE
// ==========================================

function mostrarErrorAnalisis(data, modeloNoDisponible = false) {

    // Evitar mostrar resultados anteriores como si fueran actuales
    document.getElementById("habilidadesTexto").replaceChildren();
    document.getElementById("habilidadesModelo").replaceChildren();
    document.getElementById("habilidadesAmbos").replaceChildren();
    document.getElementById("habilidadesPresentes").replaceChildren();
    document.getElementById("brechasHabilidades").replaceChildren();
    document.getElementById("recomendaciones").replaceChildren();

    document.getElementById("compatibilidadValor").textContent = "--";
    document.getElementById("compatibilidadNivel").textContent = "No disponible";
    document.getElementById("compatibilidadBarra").style.width = "0%";

    const mensaje = data.message ||
        data.error ||
        "No fue posible realizar el anÃ¡lisis.";

    if (modeloNoDisponible) {
        mostrarEstado("unavailable", mensaje);
    } else {
        mostrarEstado("error", mensaje);
    }
}


// ==========================================
// CARGAR DATOS DE LAS GRÃFICAS
// ==========================================

async function cargarDashboard() {

    const estado = document.getElementById("estadoDashboard");

    try {
        estado.textContent = "Cargando datos de demostración...";

        const response = await fetch("/api/dashboard-data");

        if (!response.ok) {
            throw new Error("No fue posible obtener los datos.");
        }

        datosDashboard = await response.json();

        if (
            !datosDashboard.perfiles ||
            !Array.isArray(datosDashboard.perfiles.perfiles) ||
            !datosDashboard.transiciones ||
            !Array.isArray(datosDashboard.transiciones.transiciones) ||
            !datosDashboard.mercado ||
            !Array.isArray(datosDashboard.mercado.ofertas_por_familia) ||
            !Array.isArray(datosDashboard.mercado.habilidades_mas_pedidas)
        ) {
            throw new Error("El formato de los datos de demostración no es válido.");
        }

        cargarPerfiles();
        dibujarTransiciones();
        dibujarMercado();

        estado.textContent = "GrÃ¡ficas cargadas correctamente.";

    } catch (error) {
        estado.textContent = "No fue posible cargar las gráficas de demostración.";
        console.error("Error del dashboard:", error);
    }
}


// ==========================================
// CARGAR PERFILES DE DEMOSTRACIÃ“N
// ==========================================

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


// ==========================================
// PRIMERA GRÃFICA: COMPATIBILIDAD
// ==========================================

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

    const detalle = document.getElementById("detalleHabilidades");
    detalle.replaceChildren();

    const titulo = document.createElement("h4");
    titulo.textContent = "Detalle de habilidades";

    const presentes = document.createElement("p");
    presentes.textContent =
        "Habilidades presentes: " +
        (familias[0]?.presentes?.join(", ") || "No disponibles");

    const faltantes = document.createElement("p");
    faltantes.textContent =
        "Habilidades por aprender: " +
        (familias[0]?.faltantes_principales?.join(", ") || "No disponibles");

    detalle.append(titulo, presentes, faltantes);
}


// ==========================================
// SEGUNDA GRÃFICA: TRANSICIONES
// ==========================================

function dibujarTransiciones() {

    const transiciones = [...datosDashboard.transiciones.transiciones]
        .sort((a, b) => b.similitud - a.similitud)
        .slice(0, 10);

    const contexto = document
        .getElementById("transicionesChart")
        .getContext("2d");

    if (transicionesChart) {
        transicionesChart.destroy();
    }

    transicionesChart = new Chart(contexto, {

        type: "bar",

        data: {
            labels: transiciones.map(
                item => `${item.origen} â†’ ${item.destino}`
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


// ==========================================
// TERCERA GRÃFICA: MERCADO LABORAL
// ==========================================

function dibujarMercado() {

    const ofertas = datosDashboard.mercado.ofertas_por_familia
        .slice()
        .sort((a, b) => b.ofertas - a.ofertas)
        .slice(0, 10);

    const contexto = document
        .getElementById("mercadoChart")
        .getContext("2d");

    if (mercadoChart) {
        mercadoChart.destroy();
    }

    mercadoChart = new Chart(contexto, {

        type: "bar",

        data: {
            labels: ofertas.map(item => item.familia),

            datasets: [{
                label: "NÃºmero de ofertas",
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


// ==========================================
// ENVIAR PERFIL A FLASK
// ==========================================

form.addEventListener("submit", async function(event) {

    event.preventDefault();

    // El nombre se conserva Ãºnicamente en el frontend
    const nombre = document.getElementById("nombre").value.trim();

    const perfil = document.getElementById("perfil").value.trim();

    const habilidades = document.getElementById("habilidades").value.trim();

    const objetivo = document.getElementById("objetivo").value;

    if (!nombre || !perfil || !habilidades || !objetivo) {

        resultado.hidden = false;
        resultado.textContent = "Completa todos los campos para continuar.";

        return;
    }

    // IMPORTANTE:
    // El nombre NO se incluye en profileText.
    const profileText = [
        `Perfil profesional: ${perfil}`,
        `Habilidades: ${habilidades}`,
        `Objetivo laboral: ${objetivo}`
    ].join("\n");

    resultado.hidden = false;
    resultado.textContent = `\u00a1Gracias, ${nombre}! Estamos preparando tu an\u00e1lisis.`;

    mostrarEstado(
        "loading",
        "Analizando tu perfil profesional. Por favor espera..."
    );

    boton.disabled = true;
    boton.textContent = "Analizando...";

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

        // El servidor informa que el modelo todavÃ­a no estÃ¡ disponible
        if (
            response.status === 503 ||
            data.status === "model_unavailable"
        ) {
            mostrarErrorAnalisis(data, true);
            return;
        }

        // Manejar errores del servidor o del anÃ¡lisis
        if (!response.ok || data.status === "error") {
            mostrarErrorAnalisis(data, false);
            return;
        }

        // Mostrar resultados recibidos
        mostrarResultadosUsuario(data);

    } catch (error) {

        mostrarErrorAnalisis({
            message: "No se pudo conectar con el servidor. Verifica tu conexiÃ³n e intÃ©ntalo nuevamente."
        });

        console.error("Error durante el anÃ¡lisis:", error);

    } finally {

        boton.disabled = false;
        boton.textContent = "Analizar mi perfil";
    }
});


// ==========================================
// INICIAR DASHBOARD
// ==========================================

cargarDashboard();




