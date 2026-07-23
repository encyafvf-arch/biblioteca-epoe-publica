import streamlit as st
import pandas as pd
import unicodedata
import os

st.set_page_config(
    page_title="Catálogo de Biblioteca - EPOE",
    page_icon="📚",
    layout="wide"
)

# Estilos CSS con Flexbox para simetría absoluta de escudos
st.markdown("""
<style>
    .header-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 35px;
        margin-top: 10px;
        margin-bottom: 25px;
        width: 100%;
    }
    .header-text {
        text-align: center;
    }
    .main-header { 
        font-size: 2.1rem; 
        color: #FFFFFF !important; 
        font-weight: 800; 
        line-height: 1.2;
        font-family: 'Arial', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .sub-header { 
        font-size: 1.15rem; 
        color: #D69E2E !important; 
        font-weight: 600;
        margin-top: 6px;
    }
    .escudo-img {
        width: 120px;
        height: auto;
        object-fit: contain;
    }
</style>
""", unsafe_allow_html=True)

# Buscar imágenes de escudos sin importar mayúsculas
def buscar_imagen(nombre_base):
    if os.path.exists("."):
        for f in os.listdir("."):
            if f.lower() == nombre_base.lower():
                return f
    return None

img_cimee = buscar_imagen("escudo_cimee.png")
img_epoe = buscar_imagen("escudo_epoe.png")

# Construcción simétrica del membrete (Flexbox puro)
html_cimee = f'<img src="data:image/png;base64,{st.image if False else ""}" class="escudo-img">' if img_cimee else ''

# Generar encabezado Streamlit
st.markdown(f"""
<div class="header-container">
    <div>{"<img src='app/static/" + img_cimee + "' class='escudo-img'>" if img_cimee else ""}</div>
    <div class="header-text">
        <div class="main-header">ESCUELA DE PERFECCIONAMIENTO DE OFICIALES DEL EJÉRCITO</div>
        <div class="sub-header">CONSULTA PÚBLICA DE CATÁLOGO BIBLIOGRÁFICO</div>
    </div>
    <div>{"<img src='app/static/" + img_epoe + "' class='escudo-img'>" if img_epoe else ""}</div>
</div>
""", unsafe_allow_html=True)

# Alternativa nativa si no carga la ruta estática HTML
if not img_cimee or not img_epoe:
    col1, col2, col3 = st.columns([1.5, 5, 1.5])
    with col1:
        if img_cimee: st.image(img_cimee, width=115)
    with col2:
        st.markdown('<div class="main-header" style="text-align:center;">ESCUELA DE PERFECCIONAMIENTO DE OFICIALES DEL EJÉRCITO</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header" style="text-align:center;">CONSULTA PÚBLICA DE CATÁLOGO BIBLIOGRÁFICO</div>', unsafe_allow_html=True)
    with col3:
        if img_epoe: st.image(img_epoe, width=115)

FILE_INVENTARIO = "inventario_libros-FABI.xlsx"

def quitar_tildes(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

@st.cache_data(ttl=300)
def cargar_catalogo_publico():
    if os.path.exists(FILE_INVENTARIO):
        try:
            df_raw = pd.read_excel(FILE_INVENTARIO, sheet_name="Registro de Libros", header=None)
            
            # Detectar fila de encabezados
            header_row = 2
            for idx, row in df_raw.iterrows():
                row_str = [str(val).lower() for val in row.values if pd.notna(val)]
                if any("titulo" in item or "título" in item or "autor" in item for item in row_str):
                    header_row = idx
                    break
            
            df = pd.read_excel(FILE_INVENTARIO, sheet_name="Registro de Libros", header=header_row)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Detección rigurosa de columnas
            col_titulo = None
            col_autor = None
            col_tema = None
            col_editorial = None
            col_estado = None

            for c in df.columns:
                c_low = c.lower()
                if any(k in c_low for k in ["titulo", "título", "nombre de obra"]) and "codigo" not in c_low and not col_titulo:
                    col_titulo = c
                elif "autor" in c_low and not col_autor:
                    col_autor = c
                elif any(k in c_low for k in ["tema", "categor", "genero", "género", "materia", "especialidad"]) and not col_tema:
                    col_tema = c
                elif "editor" in c_low and not col_editorial:
                    col_editorial = c
                elif "estado" in c_low and not col_estado:
                    col_estado = c

            # Respaldo por orden exacto de columnas si falla el nombre
            cols = list(df.columns)
            if not col_titulo and len(cols) > 1: col_titulo = cols[1]
            if not col_autor and len(cols) > 2: col_autor = cols[2]
            if not col_tema and len(cols) > 3: col_tema = cols[3]
            if not col_editorial and len(cols) > 4: col_editorial = cols[4]

            df_limpio = pd.DataFrame()
            
            df_limpio["Título del Libro"] = df[col_titulo] if col_titulo else df.iloc[:, 1]
            df_limpio["Autor(es)"] = df[col_autor] if col_autor else "-"
            df_limpio["Categoría / Género"] = df[col_tema] if col_tema else "General"
            df_limpio["Editorial"] = df[col_editorial] if col_editorial else "-"
            
            if col_estado:
                df_limpio["Estado"] = df[col_estado].fillna("Disponible").apply(
                    lambda x: "🟢 Disponible" if str(x).strip().lower() == "disponible" else "🔴 En Consulta"
                )
            else:
                df_limpio["Estado"] = "🟢 Disponible"
                
            # Limpieza básica
            df_limpio = df_limpio.fillna("-").astype(str).replace(["nan", "NaN", "None", "<NA>", "No especificado", ""], "-")
            df_limpio = df_limpio[df_limpio["Título del Libro"].str.strip() != "-"].reset_index(drop=True)
            df_limpio.insert(0, "N°", range(1, len(df_limpio) + 1))
            
            return df_limpio
        except Exception as e:
            st.error(f"Error al procesar el catálogo: {e}")
            return pd.DataFrame()
    else:
        st.error("⚠️ El catálogo bibliográfico no está disponible momentáneamente.")
        return pd.DataFrame()

df_cat = cargar_catalogo_publico()

# Métricas públicas
m1, m2 = st.columns(2)
m1.metric("Total de Títulos en Acervo", f"{len(df_cat):,}")
disponibles_count = len(df_cat[df_cat["Estado"] == "🟢 Disponible"]) if "Estado" in df_cat.columns and len(df_cat) > 0 else 0
m2.metric("Títulos Disponibles para Consulta", f"{disponibles_count:,}")

st.markdown("---")

# Buscador y Filtro por Categoría / Género
col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    busqueda = st.text_input("🔍 Búsqueda general (Título, Autor, Editorial)")
with col_s2:
    if "Categoría / Género" in df_cat.columns and len(df_cat) > 0:
        # Obtener ÚNICAMENTE las categorías reales (ej. Historia, Novela, Ensayo) evitando títulos
        valores_raw = df_cat["Categoría / Género"].unique()
        categorias_validas = sorted([
            str(v).strip() for v in valores_raw 
            if str(v).strip() not in ["", "-", "nan", "NaN", "None"] and len(str(v).strip()) < 50
        ])
        cat_list = ["Todas las Categorías / Géneros"] + categorias_validas
    else:
        cat_list = ["Todas las Categorías / Géneros"]
        
    categoria_sel = st.selectbox("Filtrar por Categoría o Género", cat_list)

df_filtrado = df_cat.copy()

# Filtrar por categoría seleccionada
if categoria_sel != "Todas las Categorías / Géneros" and len(df_filtrado) > 0:
    df_filtrado = df_filtrado[df_filtrado["Categoría / Género"].str.strip() == categoria_sel]

# Búsqueda libre por texto
if busqueda and len(df_filtrado) > 0:
    term_busqueda = quitar_tildes(busqueda)
    mask = df_filtrado.apply(
        lambda row: row.astype(str).apply(lambda val: term_busqueda in quitar_tildes(val)).any(),
        axis=1
    )
    df_filtrado = df_filtrado[mask]

st.write(f"Mostrando **{len(df_filtrado):,}** libros.")

# Tabla interactiva
st.dataframe(
    df_filtrado, 
    use_container_width=True, 
    height=500, 
    hide_index=True,
    column_config={
        "N°": st.column_config.NumberColumn("N°", width="small"),
        "Título del Libro": st.column_config.TextColumn("Título del Libro", width="large"),
        "Autor(es)": st.column_config.TextColumn("Autor(es)", width="medium"),
        "Categoría / Género": st.column_config.TextColumn("Categoría / Género", width="medium"),
        "Editorial": st.column_config.TextColumn("Editorial", width="small"),
        "Estado": st.column_config.TextColumn("Estado", width="small")
    }
)
