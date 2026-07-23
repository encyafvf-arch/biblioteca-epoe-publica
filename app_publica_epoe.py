import streamlit as st
import pandas as pd
import unicodedata
import os

st.set_page_config(
    page_title="Catálogo de Biblioteca - EPOE",
    page_icon="📚",
    layout="wide"
)

# Estilos formales
st.markdown("""
<style>
    .main-header { 
        font-size: 1.8rem; 
        color: #1B365D; 
        font-weight: 800; 
        text-align: center; 
        line-height: 1.2;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .sub-header { 
        font-size: 1.1rem; 
        color: #2C5282; 
        text-align: center; 
        font-weight: 600;
        margin-top: 5px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado con Escudos
col_esc1, col_texto, col_esc2 = st.columns([1, 4, 1])

with col_esc1:
    if os.path.exists("escudo_cimee.png"):
        st.image("escudo_cimee.png", width=110)

with col_texto:
    st.markdown('<div class="main-header">ESCUELA DE PERFECCIONAMIENTO DE OFICIALES DEL EJÉRCITO</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Consulta Pública de Catálogo Bibliográfico</div>', unsafe_allow_html=True)

with col_esc2:
    if os.path.exists("escudo_epoe.png"):
        st.image("escudo_epoe.png", width=110)

FILE_INVENTARIO = "inventario_libros-FABI.xlsx"

def quitar_tildes(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

@st.cache_data(ttl=300)
def cargar_catalogo_publico():
    if os.path.exists(FILE_INVENTARIO):
        try:
            # Leer el archivo Excel completo
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
            
            # Mapeo inteligente descartando códigos de la columna 'Título'
            col_titulo = None
            for c in df.columns:
                c_low = c.lower()
                if ("titulo" in c_low or "título" in c_low or "nombre" in c_low) and "codigo" not in c_low:
                    col_titulo = c
                    break
            
            col_autor = next((c for c in df.columns if "autor" in c.lower()), None)
            col_tema = next((c for c in df.columns if any(k in c.lower() for k in ["tema", "categor", "genero", "género", "colecc", "serie"])), None)
            col_editorial = next((c for c in df.columns if "editor" in c.lower()), None)
            col_estado = next((c for c in df.columns if "estado" in c.lower()), None)
            
            # Si no encontró por nombre, usar posiciones probables del Excel
            cols_disponibles = list(df.columns)
            if not col_titulo and len(cols_disponibles) > 1:
                # Si la col 1 es código (LIB-...), tomar la col 2 para el título real
                primer_val = str(df.iloc[0, 1]) if len(df) > 0 else ""
                col_titulo = cols_disponibles[2] if "LIB-" in primer_val and len(cols_disponibles) > 2 else cols_disponibles[1]
                
            if not col_autor and len(cols_disponibles) > 2:
                col_autor = cols_disponibles[2] if col_titulo != cols_disponibles[2] else cols_disponibles[3]
                
            if not col_tema and len(cols_disponibles) > 3:
                col_tema = cols_disponibles[3]
                
            if not col_editorial and len(cols_disponibles) > 4:
                col_editorial = cols_disponibles[4]

            df_limpio = pd.DataFrame()
            
            df_limpio["Título del Libro"] = df[col_titulo] if col_titulo else df.iloc[:, 1]
            df_limpio["Autor(es)"] = df[col_autor] if col_autor else "-"
            df_limpio["Categoría / Tema"] = df[col_tema] if col_tema else "General"
            df_limpio["Editorial"] = df[col_editorial] if col_editorial else "-"
            
            if col_estado:
                df_limpio["Estado"] = df[col_estado].fillna("Disponible").apply(
                    lambda x: "🟢 Disponible" if str(x).strip().lower() == "disponible" else "🔴 En Consulta"
                )
            else:
                df_limpio["Estado"] = "🟢 Disponible"
                
            # Limpieza general
            df_limpio = df_limpio.fillna("-").astype(str).replace(["nan", "NaN", "None", "<NA>", "No especificado", ""], "-")
            
            # Filtro para que el Título sea válido
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

# Métricas
m1, m2 = st.columns(2)
m1.metric("Total de Títulos en Acervo", f"{len(df_cat):,}")
disponibles_count = len(df_cat[df_cat["Estado"] == "🟢 Disponible"]) if "Estado" in df_cat.columns and len(df_cat) > 0 else 0
m2.metric("Títulos Disponibles para Consulta", f"{disponibles_count:,}")

st.markdown("---")

# Buscador y Filtro
col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    busqueda = st.text_input("🔍 Buscar por Título, Autor o Editorial")
with col_s2:
    if "Categoría / Tema" in df_cat.columns and len(df_cat) > 0:
        cat_list = ["Todas"] + sorted([c for c in df_cat["Categoría / Tema"].unique() if c and c != "-"])
    else:
        cat_list = ["Todas"]
    categoria_sel = st.selectbox("Filtrar por Categoría / Tema", cat_list)

df_filtrado = df_cat.copy()

if categoria_sel != "Todas" and len(df_filtrado) > 0:
    df_filtrado = df_filtrado[df_filtrado["Categoría / Tema"] == categoria_sel]

if busqueda and len(df_filtrado) > 0:
    term_busqueda = quitar_tildes(busqueda)
    mask = df_filtrado.apply(
        lambda row: row.astype(str).apply(lambda val: term_busqueda in quitar_tildes(val)).any(),
        axis=1
    )
    df_filtrado = df_filtrado[mask]

st.write(f"Mostrando **{len(df_filtrado):,}** libros.")

# Tabla
st.dataframe(
    df_filtrado, 
    use_container_width=True, 
    height=500, 
    hide_index=True,
    column_config={
        "N°": st.column_config.NumberColumn("N°", width="small"),
        "Título del Libro": st.column_config.TextColumn("Título del Libro", width="large"),
        "Autor(es)": st.column_config.TextColumn("Autor(es)", width="medium"),
        "Categoría / Tema": st.column_config.TextColumn("Categoría / Tema", width="medium"),
        "Editorial": st.column_config.TextColumn("Editorial", width="small"),
        "Estado": st.column_config.TextColumn("Estado", width="small")
    }
)
