import streamlit as st
import pandas as pd
import unicodedata
import os

st.set_page_config(
    page_title="Catálogo de Biblioteca - EPOE",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
<style>
    .main-header { font-size: 2rem; color: #1B365D; font-weight: bold; text-align: center; }
    .sub-header { font-size: 1rem; color: #4B6B94; text-align: center; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">ESCUELA DE PERFECCIONAMIENTO DE OFICIALES DEL EJÉRCITO</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Consulta Pública de Catálogo Bibliográfico</div>', unsafe_allow_html=True)

FILE_INVENTARIO = "inventario_libros-FABI.xlsx"

def quitar_tildes(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

@st.cache_data(ttl=600)
def cargar_catalogo_publico():
    if os.path.exists(FILE_INVENTARIO):
        try:
            # Leer el Excel convirtiendo todo a texto de forma segura
            df_raw = pd.read_excel(FILE_INVENTARIO, sheet_name="Registro de Libros", header=None)
            
            header_row = 2  # Fila 3 del Excel por defecto
            for idx, row in df_raw.iterrows():
                row_str = [str(val).lower() for val in row.values if pd.notna(val)]
                if any("titulo" in item or "título" in item for item in row_str):
                    header_row = idx
                    break
            
            df = pd.read_excel(FILE_INVENTARIO, sheet_name="Registro de Libros", header=header_row)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Identificar columnas por coincidencias flexibles
            col_titulo = next((c for c in df.columns if "titulo" in c.lower() or "título" in c.lower()), None)
            col_autor = next((c for c in df.columns if "autor" in c.lower()), None)
            col_tema = next((c for c in df.columns if "categor" in c.lower() or "tema" in c.lower()), None)
            col_editorial = next((c for c in df.columns if "editor" in c.lower()), None)
            col_estado = next((c for c in df.columns if "estado" in c.lower()), None)
            
            df_limpio = pd.DataFrame()
            
            df_limpio["Título del Libro"] = df[col_titulo] if col_titulo else df.iloc[:, 2 if len(df.columns) > 2 else 0]
            df_limpio["Autor(es)"] = df[col_autor] if col_autor else "No especificado"
            df_limpio["Categoría / Tema"] = df[col_tema] if col_tema else "General"
            df_limpio["Editorial"] = df[col_editorial] if col_editorial else "-"
            
            if col_estado:
                df_limpio["Estado"] = df[col_estado].fillna("Disponible").apply(
                    lambda x: "🟢 Disponible" if str(x).strip().lower() == "disponible" else "🔴 En Consulta"
                )
            else:
                df_limpio["Estado"] = "🟢 Disponible"
                
            # Limpieza integral de celdas vacías
            df_limpio = df_limpio.fillna("").astype(str).replace(["nan", "NaN", "None", "<NA>"], "")
            df_limpio = df_limpio[df_limpio["Título del Libro"].str.strip() != ""].reset_index(drop=True)
            
            # Número de orden 1, 2, 3...
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

# Buscador y Filtro por Categoría
col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    busqueda = st.text_input("🔍 Buscar por Título, Autor o Editorial")
with col_s2:
    if "Categoría / Tema" in df_cat.columns and len(df_cat) > 0:
        cat_list = ["Todas"] + sorted([c for c in df_cat["Categoría / Tema"].unique() if c])
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

# Tabla limpia
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
