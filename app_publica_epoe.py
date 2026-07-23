import streamlit as st
import pandas as pd
import unicodedata
import os

st.set_page_config(
    page_title="Catálogo de Biblioteca - EPOE",
    page_icon="📚",
    layout="wide"
)

# Estilos CSS con alineación forzada para simetría absoluta
st.markdown("""
<style>
    .main-header { 
        font-size: 1.9rem; 
        color: #FFFFFF !important; 
        font-weight: 800; 
        text-align: center; 
        line-height: 1.2;
        font-family: 'Arial', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .sub-header { 
        font-size: 1.1rem; 
        color: #D69E2E !important; 
        text-align: center; 
        font-weight: 600;
        margin-top: 6px;
        margin-bottom: 10px;
    }
    
    /* Forzar alineación a la derecha en la columna izquierda (CIMEE) */
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stImage"] {
        display: flex;
        justify-content: flex-end;
    }
    
    /* Forzar alineación a la izquierda en la columna derecha (EPOE) */
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stImage"] {
        display: flex;
        justify-content: flex-start;
    }

    div[data-testid="stImage"] > img {
        height: auto;
        object-fit: contain;
    }
</style>
""", unsafe_allow_html=True)

# Buscar escudos en carpeta
def obtener_escudo(nombre_base):
    if os.path.exists("."):
        for f in os.listdir("."):
            if f.lower() == nombre_base.lower():
                return f
    return None

img_cimee = obtener_escudo("escudo_cimee.png")
img_epoe = obtener_escudo("escudo_epoe.png")

# Proporciones reducidas [2, 5, 2] para acercar las columnas laterales al centro
col_e1, col_t, col_e2 = st.columns([2, 5, 2])

with col_e1:
    if img_cimee:
        st.image(img_cimee, width=105)

with col_t:
    st.markdown('<div class="main-header">ESCUELA DE PERFECCIONAMIENTO DE OFICIALES DEL EJÉRCITO</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">CONSULTA PÚBLICA DE CATÁLOGO BIBLIOGRÁFICO</div>', unsafe_allow_html=True)

with col_e2:
    if img_epoe:
        st.image(img_epoe, width=105)

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
            
            header_row = 2
            for idx, row in df_raw.iterrows():
                row_str = [str(val).lower() for val in row.values if pd.notna(val)]
                if any("titulo" in item or "título" in item or "autor" in item for item in row_str):
                    header_row = idx
                    break
            
            df = pd.read_excel(FILE_INVENTARIO, sheet_name="Registro de Libros", header=header_row)
            df.columns = [str(c).strip() for c in df.columns]
            
            col_titulo = next((c for c in df.columns if any(k in c.lower() for k in ["titulo", "título"]) and "codigo" not in c.lower()), None)
            col_autor = next((c for c in df.columns if "autor" in c.lower()), None)
            col_categoria = next((c for c in df.columns if any(k in c.lower() for k in ["categor", "tema", "genero", "género"])), None)
            col_editorial = next((c for c in df.columns if "editor" in c.lower()), None)
            col_estado = next((c for c in df.columns if "estado" in c.lower()), None)
            
            cols = list(df.columns)
            
            if not col_titulo or "LIB-" in str(df[col_titulo].iloc[0]):
                for c in cols:
                    val_sample = str(df[c].iloc[0]) if len(df) > 0 else ""
                    if "LIB-" not in val_sample and len(val_sample) > 5 and c != col_autor:
                        col_titulo = c
                        break
                        
            df_limpio = pd.DataFrame()
            
            df_limpio["Título del Libro"] = df[col_titulo] if col_titulo else df.iloc[:, 2]
            df_limpio["Autor(es)"] = df[col_autor] if col_autor else df.iloc[:, 3]
            df_limpio["Categoría / Género"] = df[col_categoria] if col_categoria else df.iloc[:, 4]
            df_limpio["Editorial"] = df[col_editorial] if col_editorial else df.iloc[:, 5]
            
            if col_estado:
                df_limpio["Estado"] = df[col_estado].fillna("Disponible").apply(
                    lambda x: "🟢 Disponible" if str(x).strip().lower() == "disponible" else "🔴 En Consulta"
                )
            else:
                df_limpio["Estado"] = "🟢 Disponible"
                
            df_limpio = df_limpio.fillna("-").astype(str).replace(["nan", "NaN", "None", "<NA>", "No especificado", ""], "-")
            df_limpio = df_limpio[~df_limpio["Título del Libro"].str.startswith("LIB-")].reset_index(drop=True)
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
    busqueda = st.text_input("🔍 Búsqueda general (Título, Autor, Editorial)")
with col_s2:
    if "Categoría / Género" in df_cat.columns and len(df_cat) > 0:
        cat_unicas = sorted([
            str(v).strip() for v in df_cat["Categoría / Género"].unique() 
            if str(v).strip() not in ["", "-", "nan", "NaN", "None"]
        ])
        cat_list = ["Todas las Categorías / Géneros"] + cat_unicas
    else:
        cat_list = ["Todas las Categorías / Géneros"]
        
    categoria_sel = st.selectbox("Filtrar por Categoría o Género", cat_list)

df_filtrado = df_cat.copy()

if categoria_sel != "Todas las Categorías / Géneros" and len(df_filtrado) > 0:
    df_filtrado = df_filtrado[df_filtrado["Categoría / Género"].str.strip() == categoria_sel]

if busqueda and len(df_filtrado) > 0:
    term_busqueda = quitar_tildes(busqueda)
    mask = df_filtrado.apply(
        lambda row: row.astype(str).apply(lambda val: term_busqueda in quitar_tildes(val)).any(),
        axis=1
    )
    df_filtrado = df_filtrado[mask]

st.write(f"Mostrando **{len(df_filtrado):,}** libros.")

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
