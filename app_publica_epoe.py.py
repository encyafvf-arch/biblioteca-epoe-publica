import streamlit as st
import pandas as pd
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

@st.cache_data(ttl=600)
def cargar_catalogo_publico():
    if os.path.exists(FILE_INVENTARIO):
        try:
            df = pd.read_excel(FILE_INVENTARIO, sheet_name="Registro de Libros", header=2)
            df.columns = df.columns.str.strip()
            
            # Garantizar columnas públicas
            if "Estado" not in df.columns:
                df["Estado"] = "Disponible"
            else:
                df["Estado"] = df["Estado"].fillna("Disponible")
                
            # Mapear estado público para no dar detalles internos
            df["Estado Público"] = df["Estado"].apply(
                lambda x: "🟢 Disponible" if str(x).strip().lower() == "disponible" else "🔴 En Consulta / Prestado"
            )
            
            cols_publicas = [
                'Código Topográfico / ID', 'Título del Libro', 'Autor(es)', 
                'Categoría / Tema', 'Colección / Serie', 'Editorial', 
                'Ubicación en Estante', 'Estado Público'
            ]
            
            # Filtrar estrictamente solo las columnas públicas existentes
            cols_existentes = [c for c in cols_publicas if c in df.columns]
            df_publico = df[cols_existentes].reset_index(drop=True)
            df_publico = df_publico.fillna("").astype(str).replace(["nan", "NaN", "None"], "")
            return df_publico
        except Exception as e:
            st.error("Error al cargar el catálogo público.")
            return pd.DataFrame()
    else:
        st.error("⚠️ El catálogo bibliográfico no está disponible momentáneamente.")
        return pd.DataFrame()

df_cat = cargar_catalogo_publico()

# Métricas públicas básicas
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
    cat_list = ["Todas"] + list(df_cat["Categoría / Tema"].unique()) if "Categoría / Tema" in df_cat.columns else ["Todas"]
    categoria_sel = st.selectbox("Filtrar por Categoría / Tema", cat_list)

df_filtrado = df_cat.copy()

if categoria_sel != "Todas" and "Categoría / Tema" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Categoría / Tema"] == categoria_sel]

if busqueda:
    mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
    df_filtrado = df_filtrado[mask]

st.write(f"Mostrando **{len(df_filtrado):,}** libros.")
st.dataframe(df_filtrado, use_container_width=True, height=500, hide_index=True)