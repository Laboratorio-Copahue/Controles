import streamlit as st
import pandas as pd
from reporte_farmacity.report_maker import generar_reportes

def render_farmacity_page():
    st.title("🛒 Reporte Faltantes Farmacity")
    st.write("Sube tu archivo CSV para detectar automáticamente los productos y generar los reportes.")

    uploaded_file = st.file_uploader("Cargar archivo CSV", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=',', encoding='latin1')

        st.success("¡Archivo cargado correctamente!")

        if st.button("Generar Reporte"):
            df_resumen, _ = generar_reportes(df)
            
            st.success("¡Reportes generados con éxito!")

            col1, col2 = st.columns(2)
            with col1:
                with open("reporte_farmacity.docx", "rb") as f:
                    st.download_button("📥 Descargar Word", f, file_name="Reporte_Farmacity.docx")
            with col2:
                with open("reporte_farmacity.xlsx", "rb") as f:
                    st.download_button("📥 Descargar Excel", f, file_name="Resumen_Faltantes.xlsx")