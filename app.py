import streamlit as st
import pandas as pd
import zipfile
import xml.etree.ElementTree as ET
import io

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Stock y Reorden - Salud",
    layout="wide",
    page_icon="📦"
)

st.title("📦 Dashboard de Control de Stock y Reorden de Insumos")
st.markdown("Carga las planillas brutas exportadas de tu sistema para calcular automáticamente los niveles de reorden y alertas de compra.")

# -----------------------------------------------------------------------------
# Función para leer archivos Excel corruptos o con estilos no estándar
# -----------------------------------------------------------------------------
def leer_excel_robusto(file_bytes):
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as z:
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                for elem in tree.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                    text = "".join([t.text for t in elem.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t.text])
                    shared_strings.append(text)

            ws_tree = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
            rows_data = []
            for row in ws_tree.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                row_cells = []
                for cell in row.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                    t = cell.attrib.get('t', '')
                    v_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                    val = v_elem.text if v_elem is not None else None
                    if val is not None and t == 's':
                        val = shared_strings[int(val)]
                    row_cells.append(val)
                rows_data.append(row_cells)
            return rows_data
    except Exception as e:
        st.error(f"Error al procesar la estructura interna del archivo: {e}")
        return []

# -----------------------------------------------------------------------------
# Interfaz de Carga de Archivos
# -----------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    file_stock = st.file_uploader("1. Subir Planilla de Stock Actual (.xlsx)", type=["xlsx"])

with col2:
    file_mov = st.file_uploader("2. Subir Planilla de Movimientos Trimestrales (.xlsx)", type=["xlsx"])

# -----------------------------------------------------------------------------
# Parámetros en la Barra Lateral
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Parámetros de Compra")
lead_time_dias = st.sidebar.number_input("Tiempo de Entrega del Proveedor (Días)", min_value=1, value=5)
factor_seguridad = st.sidebar.slider("Factor de Stock de Seguridad", min_value=1.0, max_value=2.5, value=1.5, step=0.1)

# -----------------------------------------------------------------------------
# Procesamiento de Datos
# -----------------------------------------------------------------------------
if file_stock and file_mov:
    # 1. Procesar datos de Stock Actual
    rows_stock = leer_excel_robusto(file_stock.read())    
    print(rows_stock.pop(0))
    stock_data = []
    for r in rows_stock:
        if len(r) >= 5 and r[2] and r[11]:
            try:
                stock_data.append({'ID_Producto': str(r[2]).strip(), 'Stock_Actual': float(r[11])})
            except ValueError:
                pass
    
    if not stock_data:
        st.warning("No se pudieron extraer datos válidos de la planilla de Stock Actual.")
        st.stop()

    df_stock = pd.DataFrame(stock_data).groupby('ID_Producto', as_index=False)['Stock_Actual'].sum()

    # 2. Procesar datos de Movimientos Trimestrales
    rows_mov = leer_excel_robusto(file_mov.read())
    mov_data = []
    for r in rows_mov:
        if len(r) > 10 and r[2] and r[10]:
            try:
                mov_data.append({'ID_Producto': str(r[2]).strip(), 'Consumo_Trimestral': float(r[10])})
            except ValueError:
                pass

    df_mov = pd.DataFrame(mov_data).groupby('ID_Producto', as_index=False)['Consumo_Trimestral'].sum()

    # 3. Consolidación y Cruce de Datos
    df = pd.merge(df_stock, df_mov, on='ID_Producto', how='outer').fillna(0)

    # 4. Cálculos Automáticos de KPIs
    df['CAD (Consumo Diario)'] = (df['Consumo_Trimestral'] / 90.0).round(2)
    df['Stock Critico'] = (df['CAD (Consumo Diario)'] * lead_time_dias).round(1)
    df['Stock Minimo'] = (df['Stock Critico'] * factor_seguridad).round(1)

    def determinar_estado(row):
        if row['Stock_Actual'] < row['Stock Critico']:
            return '🔴 CRÍTICO'
        elif row['Stock_Actual'] <= row['Stock Minimo']:
            return '🟡 REORDEN'
        else:
            return '🟢 ÓPTIMO'

    df['Estado'] = df.apply(determinar_estado, axis=1)

    df['Cantidad a Pedir'] = df.apply(
        lambda r: round(max(0, (r['Stock Minimo'] * 2) - r['Stock_Actual'])) if r['Estado'] != '🟢 ÓPTIMO' else 0,
        axis=1
    )

    # -------------------------------------------------------------------------
    # Visualización de Métricas e Indicadores
    # -------------------------------------------------------------------------
    st.divider()
    st.subheader("📊 Indicadores Globales de Inventario")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_prod = len(df)
    criticos = len(df[df['Estado'] == '🔴 CRÍTICO'])
    reorden = len(df[df['Estado'] == '🟡 REORDEN'])
    optimos = len(df[df['Estado'] == '🟢 ÓPTIMO'])

    kpi1.metric("Total Productos", total_prod)
    kpi2.metric("🚨 Pedido Urgente (Críticos)", criticos)
    kpi3.metric("⚠️ Punto de Reorden", reorden)
    kpi4.metric("✅ Nivel Óptimo", optimos)

    # -------------------------------------------------------------------------
    # Tabla Interactiva y Exportación
    # -------------------------------------------------------------------------
    st.divider()
    st.subheader("📋 Lista de Control y Solicitud de Pedidos")

    filtro_estado = st.multiselect(
        "Filtrar por Estado:",
        options=['🔴 CRÍTICO', '🟡 REORDEN', '🟢 ÓPTIMO'],
        default=['🔴 CRÍTICO', '🟡 REORDEN']
    )

    df_filtrado = df[df['Estado'].isin(filtro_estado)]
    st.dataframe(df_filtrado, use_container_width=True)

    # Botón para descargar reporte consolidado en Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_filtrado.to_excel(writer, index=False, sheet_name='Solicitud_Insumos')

    st.download_button(
        label="📥 Descargar Solicitud de Pedidos en Excel",
        data=buffer.getvalue(),
        file_name="Solicitud_Insumos_Salud.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("ℹ️ Por favor, sube los dos archivos de Excel arriba para generar el análisis automático.")