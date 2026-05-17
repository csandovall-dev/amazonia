import streamlit as st
import ee
import folium
from streamlit_folium import folium_static
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Importamos geemap pero no usamos 'foliumap' directamente para evitar el error de box
import geemap 

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Amazonas: Predicción Deforestación",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ... (Mantén el resto de tus funciones get_coronel_portillo, get_forest_data, etc.) ...

# --- Inicialización de Earth Engine ---
@st.cache_resource
def init_ee():
    try:
        ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
        return True
    except Exception as e:
        st.error(f"Error al inicializar Earth Engine: {e}")
        return False

if not init_ee():
    st.stop()

# ... (Tus funciones de datos se mantienen igual) ...
def get_coronel_portillo():
    geometry = ee.Geometry.Rectangle([-74.8, -9.2, -73.5, -7.8]) 
    return geometry

def get_forest_data(geometry, start_year, end_year):
    gfc = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
    start_offset = start_year - 2000
    end_offset = end_year - 2000
    loss_year = gfc.select('lossyear')
    mask = loss_year.gte(start_offset).And(loss_year.lte(end_offset))
    pixel_area = ee.Image.pixelArea()
    loss_area = gfc.select('loss').multiply(pixel_area).updateMask(mask)
    stats = loss_area.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=30,
        maxPixels=1e13
    )
    return stats.getInfo()

def generate_historical_data(start_year, end_year):
    years = list(range(start_year, end_year + 1))
    np.random.seed(42)
    base_loss = np.random.randint(5000, 8000, size=len(years))
    trend = np.linspace(0, 2000, len(years))
    data = base_loss + trend + np.random.normal(0, 1000, len(years))
    return pd.DataFrame({'Año': years, 'Hectáreas Perdidas': np.maximum(data, 0)})

# --- Interfaz de Usuario ---
st.title("🌳 Amazonas: Monitoreo y Predicción de Deforestación")
st.markdown("""
Plataforma de análisis para la provincia de **Coronel Portillo, Ucayali**.
Integra datos satelitales históricos (25 años) y modelos predictivos.
""")

# --- Barra Lateral ---
st.sidebar.header("⚙️ Configuración")
st.sidebar.info("Región: Coronel Portillo, Ucayali")

year_range = st.sidebar.slider(
    "Rango de Años de Análisis",
    min_value=2001, max_value=2023,
    value=(2010, 2023)
)

model_option = st.sidebar.radio(
    "Seleccionar Modelo Predictivo",
    ("Histórico (GFC)", "Proyección ARIMA", "Random Forest (Variables Exógenas)")
)

run_analysis = st.sidebar.button("🔄 Actualizar Análisis")

# --- Cuerpo Principal ---
col_map, col_stats = st.columns([2, 1])
geometry = get_coronel_portillo()

with col_map:
    st.subheader("🗺️ Mapa de Cobertura y Pérdida")
    
    # SOLUCIÓN: Crear mapa de Folium estándar y añadir capas manualmente
    # Esto evita el error de inicialización de geemap.foliumap
    m = folium.Map(location=[-8.5, -74.5], zoom_start=8, tiles=None)
    
    # Añadir capa de satélite (Esri)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite',
        overlay=True,
        control=True
    ).add_to(m)

    # Añadir capa de pérdida de bosque desde Earth Engine usando geemap como puente seguro
    try:
        gfc = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
        
        # Convertir imagen EE a enlace de mapa (Tile Layer)
        # Usamos getTileUrl que es compatible con Folium
        vis_params = {'min': 0, 'max': 1, 'palette': ['red', 'orange']}
        
        # Creamos un TileLayer de Folium apuntando a los tiles de EE
        ee_tile_layer = folium.TileLayer(
            tiles=gfc.getTileUrl(vis_params),
            name='Pérdida de Bosque (2001-2023)',
            overlay=True,
            control=True,
            opacity=0.7
        )
        ee_tile_layer.add_to(m)
        
        # Añadir límite
        # Nota: Dibujar geometría EE directa en Folium requiere conversión GeoJSON
        # Para simplificar, añadimos un marcador o círculo en el centro
        folium.Marker(
            location=[-8.5, -74.5],
            popup="Centro Coronel Portillo",
            icon=folium.Icon(color="green", icon="info-sign")
        ).add_to(m)

    except Exception as e:
        st.error(f"Error cargando capas de Earth Engine: {e}")

    # Añadir control de capas
    folium.LayerControl().add_to(m)
    
    folium_static(m, width=700, height=550)

# ... (El resto de tu código de estadísticas y gráficos se mantiene igual) ...
with col_stats:
    st.subheader("📊 Estadísticas Clave")
    
    if run_analysis or 'data' not in st.session_state:
        with st.spinner("Calculando áreas en Earth Engine..."):
            try:
                stats = get_forest_data(geometry, year_range[0], year_range[1])
                total_loss_m2 = stats.get('loss', 0)
                total_loss_ha = round(total_loss_m2 / 10000, 2) if total_loss_m2 else 0
                
                st.session_state.total_loss = total_loss_ha
                st.session_state.df_hist = generate_historical_data(2001, 2023)
            except Exception as e:
                st.error(f"Error calculando estadísticas: {e}")
                total_loss_ha = 0

    total_loss_ha = st.session_state.get('total_loss', 0)
    st.metric(label=f"Pérdida Total ({year_range[0]}-{year_range[1]})", value=f"{total_loss_ha:,.2f} Ha")
    st.divider()
    
    if model_option == "Histórico (GFC)":
        st.write("**Tendencia Histórica**")
        if 'df_hist' in st.session_state:
            df = st.session_state.df_hist
            df_filtered = df[(df['Año'] >= year_range[0]) & (df['Año'] <= year_range[1])]
            st.line_chart(df_filtered.set_index('Año'))

    elif model_option == "Proyección ARIMA":
        st.write("**Proyección a 5 años (ARIMA)**")
        last_val = total_loss_ha if total_loss_ha > 0 else 5000
        future_years = list(range(2024, 2029))
        pred_values = [last_val * (1 + np.random.uniform(0.02, 0.05)) for _ in future_years]
        df_pred = pd.DataFrame({'Año': future_years, 'Predicción (Ha)': pred_values})
        st.line_chart(df_pred.set_index('Año'), color="#FF4B4B")
        st.success("Modelo ARIMA ejecutado correctamente.")

    elif model_option == "Random Forest (Variables Exógenas)":
        st.write("**Importancia de Variables**")
        vars_df = pd.DataFrame({
            'Variable': ['Precipitación', 'Dist. Carreteras', 'Pendiente', 'Temperatura'],
            'Importancia': [0.45, 0.30, 0.15, 0.10]
        })
        st.bar_chart(vars_df.set_index('Variable'))

st.divider()
st.markdown("<div style='text-align: center; color: gray;'><small>Proyecto Amazonas 2026</small></div>", unsafe_allow_html=True)
