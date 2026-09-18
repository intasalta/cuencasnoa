# 🌊 Cuencas Hídricas del NOA - Dashboard Interactivo

Dashboard moderno, ágil y visual para la exploración cartográfica y técnica de las **85 subcuencas** y **16 macrocuencas** del Noroeste Argentino (NOA), desarrollado a partir del trabajo técnico de caracterización de cuencas de **INTA EEA Salta** (*Paoli H., Elena H., Mosciaro J., Ledesma F., Noé Y.*).

---

## ✨ Características Principales

- 🗺️ **Cartografía GIS Interactiva**: Visualizador sobre mapa interactivo con múltiples mapas base (Satélite Esri de alta resolución, Relieve Topográfico OpenTopoMap, Carto Dark y OpenStreetMap).
- 📦 **Diseño Moderno de "Cajitas" (Bento Grid)**:
  - **Morfometría**: Superficie ($km^2$), Perímetro ($km$), Longitud axial mayor ($km$) y Ancho medio ($km$).
  - **Hipsometría y Relieve**: Rango altitudinal (mínima, media, máxima, desvío estándar) y pendientes (%) con clasificación de relieve INTA.
  - **Comportamiento Hidrológico**: Índice de Compacidad de Gravelius ($K_c$) y Factor de Forma de Horton ($K_f$) con interpretación técnica de respuesta ante crecidas.
  - **Síntesis Descriptiva del Sistema Hídrico**: Texto completo, limpio y estructurado extraído de los informes PDF (dinámica de afluentes, escurrimientos y cabeceras).
  - **Galería de Mapas del Informe**: Visor de mapas temáticos (Ubicación, Flujos y Pendientes) con opción de pantalla completa sin necesidad de abrir archivos externos.
  - **Comparativa por Macrocuenca**: Gráfico de barras interactivo con todas las subcuencas tributarias del mismo sistema.
- 🔍 **Búsqueda Inteligente**: Búsqueda en tiempo real con autocompletado por nombre de subcuenca o macrocuenca.
- 🏷️ **Filtro por Cuencas Mayores**: Exploración focalizada en cualquiera de las 16 macrocuencas de la región.

---

## 🚀 Uso Local (En tu computadora)

### Opción 1: Un solo clic (Recomendada en Windows)
Haz doble clic sobre el archivo:
```text
iniciar_dashboard.bat
```
El navegador web se abrirá automáticamente en `http://localhost:8080/index.html`.

### Opción 2: Desde la terminal
```bash
python run_dashboard.py
```

---

## 🌐 Publicación en GitHub Pages (Paso a paso)

Este dashboard es **100% estático**, por lo que funciona de manera nativa y gratuita en **GitHub Pages**:

1. **Crear repositorio en GitHub**:
   - Ingresa a [github.com/new](https://github.com/new) y crea un nuevo repositorio (por ejemplo: `cuencas-noa`).
2. **Subir los archivos del proyecto**:
   ```bash
   git init
   git add .
   git commit -m "Publicación inicial del Dashboard de Cuencas del NOA"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/cuencas-noa.git
   git push -u origin main
   ```
3. **Activar GitHub Pages**:
   - Ve a la pestaña **Settings** (Configuración) de tu repositorio en GitHub.
   - En el menú lateral izquierdo, haz clic en **Pages**.
   - En **Build and deployment > Source**, selecciona `Deploy from a branch`.
   - En **Branch**, selecciona `main` y la carpeta `/ (root)`.
   - Haz clic en **Save** (Guardar).
4. **¡Listo!**:
   En 1 a 2 minutos, tu dashboard estará publicado y accesible públicamente en:
   ```text
   https://TU_USUARIO.github.io/cuencas-noa/
   ```

---

## 📂 Estructura del Proyecto

```text
anti_cuencasnoa/
├── index.html                   # Interfaz web y dashboard interactivo
├── run_dashboard.py             # Servidor web local ultraligero
├── iniciar_dashboard.bat        # Lanzador de 1 clic para Windows
├── extract_and_build.py         # Pipeline de extracción de PDFs y GeoJSON
├── data/
│   ├── cuencas_data.json        # Base de datos JSON con la síntesis y morfometría
│   └── cuencas_web.geojson      # Capa cartográfica GeoJSON optimizada para web
├── assets/
│   └── figures/                 # Mapas temáticos extraídos de los informes (JPG optimizados)
├── cuencasnoa_js.geojson        # Capa original GeoJSON
└── *.pdf                        # 100 informes técnicos originales
```

---

## 📚 Créditos y Referencias Técnicas
- **Autores**: Paoli H., Elena H., Mosciaro J., Ledesma F., Noé Y.
- **Institución**: Instituto Nacional de Tecnología Agropecuaria (INTA) - Estación Experimental Agropecuaria Salta (EEA Salta).
- **Publicación**: *Caracterización de las cuencas hídricas de las provincias de Salta y Jujuy* (2011).
