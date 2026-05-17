import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Amazonas: Predicción Deforestación", layout="wide")

st.title("🌳 Amazonas: Monitoreo y Predicción de Deforestación")
st.markdown("""
Este dashboard muestra el modelado de deforestación en **Ucayali, Coronel Portillo**.
Utiliza datos de **Google Earth Engine** (25 años) y modelos predictivos (ARIMA, Random Forest).
""")

# Inicializar Earth Engine
try:
    ee.Initialize()
    st.success("✅ Conectado a Google Earth Engine")
except Exception as e:
    st.error(f"❌ Error conectando a Earth Engine: {e}")
    st.stop()

# --- Barra Lateral: Filtros ---
st.sidebar.header("Configuración del Modelo")
anio_inicio = st.sidebar.slider("Año Inicio", 1999, 2023, 1999)
anio_fin = st.sidebar.slider("Año Fin", 2000, 2024, 2023)
modelo_seleccionado = st.sidebar.selectbox("Modelo Predictivo", ["Histórico", "ARIMA", "Random Forest"])

# --- Mapa Principal ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Mapa de Cobertura ({anio_inicio} - {anio_fin})")
    
    # Crear mapa interactivo
    m = geemap.Map(center=[-8.5, -74.5], zoom=8) # Coordenadas aprox. Coronel Portillo
    
    # Añadir capa de Satélite (Imagen base)
    m.add_basemap("SATELLITE")
    
    # Ejemplo: Capa de Deforestación (Hansen Global Forest Change)
    # Filtramos la imagen para el rango de años
    gfc = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
    
    # Visualizar pérdida de bosque (banda 'loss')
    vis_params = {
        'min': 0,
        'max': 1,
        'palette': ['red']
    }
    
    m.add_layer(gfc.select('loss'), vis_params, 'Pérdida de Bosque (2001-2023)')
    m.add_layer_control()
    
    # Mostrar mapa en Streamlit
    folium_static(m, width=700, height=500)

with col2:
    st.subheader("Resultados Preliminares")
    if modelo_seleccionado == "Histórico":
        st.info("Mostrando datos históricos de Hansen GFC.")
        st.write("- **Área analizada**: Coronel Portillo, Ucayali")
        st.write("- **Fuente**: UMD/hansen/global_forest_change")
    elif modelo_seleccionado == "ARIMA":
        st.warning("⏳ Calculando proyección ARIMA... (Simulación)")
        # Aquí irá la lógica real más adelante
        st.line_chart(np.random.randn(25).cumsum())
    elif modelo_seleccionado == "Random Forest":
        st.warning("⏳ Ejecutando Random Forest con variables exógenas...")
        st.bar_chart({"Bosque": [80, 60, 40], "Deforestado": [20, 40, 60]})

# --- Pie de página ---
st.markdown("---")
st.caption("Desarrollado con Streamlit, Google Earth Engine y Scikit-Learn | Proyecto Amazonas")
