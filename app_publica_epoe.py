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
            df = pd.read_excel(FILE_INVENTARIO, sheet_name="Registro de Libros", header=2)
            df.columns = df.columns.str.strip()
            
            # Crear columna de Estado Público
            if "Estado" in df.columns:
                df["Estado Público"] = df["Estado"].fillna("Disponible").apply(
                    lambda x: "🟢 Disponible" if str(x).strip().lower() == "disponible" else "🔴 En Consulta / Prestado"
                )
                df = df.drop(columns=["Estado"], errors="ignore")
            else:
                df["Estado Público"] = "🟢 Disponible"
            
            # Lista explícita de columnas a mostrar al público
            columnas_deseadas = [
                'Código Topográfico / ID', 
                'Título del Libro', 
                'Autor(es)', 
                'Categoría / Tema', 
                'Editorial', 
                'Ubicación en Estante', 
                'Estado Público'
            ]
            
            # Filtrar solo las columnas que existan en el Excel
            cols_finales = [c for c in columnas_deseadas if c in df.columns]
            
            # Si por alguna razón no detectó los nombres exactos, tomar todas las columnas de Excel
            if len(cols_finales) <= 1:
                cols_finales = list(df.columns)
                
            df_publico = df[cols_finales].copy()
            df_publico = df_publico.reset_index(drop=True)
            df_publico.columns = [str(c) for c in df_publico.columns]
            df_publico = df_publico.fillna("").astype(str).replace(["nan", "NaN", "None"], "")
            
            return df_publico
        except Exception as e:
            st.error(f"Error al cargar el catálogo: {e}")
            return pd.DataFrame()
    else:
        st.error("⚠️ El catálogo bibliográfico no está disponible momentáneamente.")
        return pd.DataFrame()

df_cat = cargar_catalogo_publico()

# Métricas públicas
m1, m2 = st.columns(2)
m1.metric("Total de Títulos en Acervo", f"{len(df_cat):,}")
disponibles_count = len(df_cat[df_cat["Estado Público"] == "🟢 Disponible"]) if "Estado Público" in df_cat.columns else 0
m2.metric("Títulos Disponibles para Consulta", f"{disponibles_count:,}")

st.markdown("---")

# Buscador y Filtros
col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    busqueda = st.text_input("🔍 Buscar por Título, Código, Autor o Editorial")
with col_s2:
    col_categoria = "Categoría / Tema" if "Categoría / Tema" in df_cat.columns else df_cat.columns[0]
    cat_list = ["Todas"] + list(df_cat[col_categoria].unique()) if col_categoria in df_cat.columns else ["Todas"]
    categoria_sel = st.selectbox("Filtrar por Categoría / Tema", cat_list)

df_filtrado = df_cat.copy()

if categoria_sel != "Todas" and col_categoria in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[col_categoria] == categoria_sel]

# Búsqueda flexible (sin importar tildes)
if busqueda:
    term_busqueda = quitar_tildes(busqueda)
    mask = df_filtrado.apply(
        lambda row: row.astype(str).apply(lambda val: term_busqueda in quitar_tildes(val)).any(),
        axis=1
    )
    df_filtrado = df_filtrado[mask]

st.write(f"Mostrando **{len(df_filtrado):,}** libros.")

# Tabla con todas las columnas
st.dataframe(df_filtrado, use_container_width=True, height=500, hide_index=True)
