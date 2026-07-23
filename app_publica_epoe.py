import streamlit as st
import pandas as pd
import unicodedata
import os
import base64

# Configuración de página
st.set_page_config(
    page_title="Consulta de Biblioteca - EPOE",
    page_icon="📚",
    layout="wide"
)

def quitar_tildes(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def obtener_escudo(nombre_base):
    if os.path.exists("."):
        for f in os.listdir("."):
            if f.lower() == nombre_base.lower():
                return f
    return None

img_epoe = obtener_escudo("escudo_epoe.png")

img_html = ""
if img_epoe:
    with open(img_epoe, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        img_html = f'<img src="data:image/png;base64,{encoded_string}" style="width: 100px; height: auto; display: block; margin: 0 auto 10px auto;">'

st.markdown("""
<style>
    .header-box {
        width: 100%;
        text-align: center;
        margin-top: 5px;
        margin-bottom: 20px;
    }
    .main-header { 
        font-size: 1.8rem; 
        color: #3182CE !important; 
        font-weight: 800; 
        text-align: center; 
        line-height: 1.2;
        font-family: 'Arial', sans-serif;
        text-transform: uppercase;
    }
    .sub-header { 
        font-size: 1.0rem; 
        color: #A0AEC0 !important; 
        text-align: center; 
        font-weight: 500;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="header-box">
    {img_html}
    <div class="main-header">ESCUELA DE PERFECCIONAMIENTO DE OFICIALES DEL EJÉRCITO</div>
    <div class="sub-header">Consulta Pública de Catálogo Bibliográfico (EPOE)</div>
</div>
""", unsafe_allow_html=True)

FILE_INVENTARIO = "inventario_libros-FABI.xlsx"
FILE_HISTORICO = "historico_movimientos.xlsx"

# Cargar Inventario unificado exactamente igual a la app interna
def cargar_inventario_definitivo():
    archivos = [FILE_INVENTARIO, "inventario_libros.xlsx"]
    for arch in archivos:
        if os.path.exists(arch):
            try:
                df_raw = pd.read_excel(arch, sheet_name="Registro de Libros", header=None)
                df_clean = df_raw.iloc[1:, 1:10].copy()
                df_clean.columns = ['Código', 'Título del Libro', 'Autor', 'Colección', 'Tomo', 'Editorial', 'Categoría', 'Estado Local', 'Ubicación']
                df_clean = df_clean.dropna(subset=['Título del Libro']).reset_index(drop=True)
                df_clean = df_clean.fillna("-").astype(str)
                return df_clean
            except Exception:
                pass
    return pd.DataFrame()

# Cargar préstamos activos directamente desde el archivo histórico
def obtener_prestamos_activos():
    if os.path.exists(FILE_HISTORICO):
        try:
            df_h = pd.read_excel(FILE_HISTORICO)
            if not df_h.empty and "Estado" in df_h.columns and "Título del Libro" in df_h.columns:
                prestados = df_h[df_h["Estado"] == "En Préstamo"]["Título del Libro"].str.strip().tolist()
                return set(prestados)
        except Exception:
            pass
    return set()

df_libros = cargar_inventario_definitivo()
libros_prestados_set = obtener_prestamos_activos()

tot_libros = len(df_libros)
cant_prestados = len(libros_prestados_set)
lib_disponibles = max(0, tot_libros - cant_prestados)

# Actualizar la columna Estado para el público en tiempo real
if not df_libros.empty:
    df_libros["Estado"] = df_libros["Título del Libro"].apply(
        lambda t: "En Préstamo" if str(t).strip() in libros_prestados_set else "Disponible"
    )

# --- TARJETAS DE MÉTRICAS VISIBLES EN PANTALLA PRINCIPAL ---
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total de Títulos en Acervo", f"{tot_libros:,}")
with m2:
    st.metric("Libros Disponibles", f"{lib_disponibles:,}")
with m3:
    st.metric("Libros en Préstamo", f"{cant_prestados}")

st.markdown("<br>", unsafe_allow_html=True)
st.subheader("🔍 Catálogo General de Consultas (Ubicación de Libros en Estantes)")

if not df_libros.empty:
    busqueda = st.text_input(
        "🔎 Buscar por Título, Autor, Colección, Editorial, Categoría o Código:",
        placeholder="Ej: Guerra, Alcibiades, Ensayo, LIB-LIT-006..."
    )
    
    cols_mostrar = ['Código', 'Título del Libro', 'Autor', 'Colección', 'Tomo', 'Editorial', 'Categoría', 'Estado', 'Ubicación']
    df_publico = df_libros[[c for c in cols_mostrar if c in df_libros.columns]]
    
    if busqueda.strip():
        b_norm = quitar_tildes(busqueda.strip())
        mask = df_publico.apply(
            lambda row: any(b_norm in quitar_tildes(str(val)) for val in row.values),
            axis=1
        )
        df_filtrado = df_publico[mask]
        st.caption(f"Se encontraron **{len(df_filtrado)}** resultado(s) para la búsqueda: *\"{busqueda}\"*")
        st.dataframe(df_filtrado, use_container_width=True, height=480, hide_index=True)
    else:
        st.caption(f"Mostrando el acervo completo (**{tot_libros:,}** libros). Use el campo superior para filtrar.")
        st.dataframe(df_publico, use_container_width=True, height=520, hide_index=True)
else:
    st.warning("No se pudo cargar la base de inventario del catálogo.")
