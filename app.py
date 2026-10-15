import streamlit as st
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def verificar_autenticacion():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if st.session_state["autenticado"]:
        return True

    st.title("Acceso Administrativo")
    
    with st.form("login_form"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar sesión")

        if submit:
            admin_user = st.secrets.get("usuario", None)
            admin_pass = st.secrets.get("contrasenia", None)

            if not admin_user or not admin_pass:
                st.error("No se encontraron las credenciales de administración en st.secrets.")

            if usuario == admin_user and password == admin_pass:
                st.session_state["autenticado"] = True
                st.success("¡Bienvenido!")
                st.rerun()  # Recarga la app para mostrar el contenido protegido
            else:
                st.error("Usuario o contraseña incorrectos.")

    return False


if verificar_autenticacion():
    # Botón de cierre de sesión en la barra lateral
    if st.sidebar.button("Cerrar sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

    st.title("Panel de Control - Administración")
    st.write("Carga de datos, métricas y reportes protegidos.")

    st.set_page_config(page_title="Gestión de Stock Crítico por Genérico ", layout="wide")



    # Función para enviar el correo electrónico
    def enviar_correo_alerta(destinatario, tabla_criticos, tabla_pedidos):
        remitente = st.secrets.get("email_usuario", None)
        password = st.secrets.get("email_contrasenia", None)

        if not remitente or not password:
            st.error("No se encotraron datos del remitente")
        
        msg = MIMEMultipart()
        msg['From'] = remitente
        msg['To'] = destinatario
        msg['Subject'] = "🚨 ALERTA: Reporte Urgente de Stock Crítico y Pedidos por Genérico - Hospital Grierson"
        
        html = f"""
        <html>
        <body>
            <h2>🏥 Reporte Automatizado de Farmacia (Unificado por Genérico)</h2>
            <p>Hola, se ha generado un nuevo análisis de inventario consolidado por Principio Activo/Genérico:</p>
            
            <h3 style="color: red;">🚨 GENÉRICOS EN STOCK CRÍTICO (Menos de 10 días de cobertura)</h3>
            {tabla_criticos.to_html(index=False)}
            
            <br>
            <h3 style="color: orange;">⚠️ GENÉRICOS QUE NECESITAN PEDIDO DE COMPRA</h3>
            {tabla_pedidos.to_html(index=False)}
            
            <br>
            <p><i>Por favor, emita las órdenes de compra correspondientes considerando que los proveedores demoran 7 días hábiles en reponer.</i></p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))
        
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(remitente, password)
            server.sendmail(remitente, destinatario, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            st.sidebar.error(f"Error de envío: {e}")
            return False



    st.title("🏥 Core Control: Alertas de Stock por Genérico")
    st.markdown("---")

    # Carga de archivos
    col1, col2 = st.columns(2)
    with col1:
        archivo_stock = st.file_uploader("📋 1. Sube el reporte de Stock Actual (Auditoría)", type=["csv", "xlsx"])
    with col2:
        archivo_movimientos = st.file_uploader("🔄 2. Sube el reporte de Movimientos (Últimos 3 meses)", type=["csv", "xlsx"])

    if archivo_stock and archivo_movimientos:
        try:
            # Lectura con calamine para evitar errores de formatos/estilos
            df_stock = pd.read_excel(archivo_stock, engine='calamine')
            df_mov = pd.read_excel(archivo_movimientos, engine='calamine')
            
            # Homologamos la columna 'Generico' a texto limpio para agrupar sin errores
            df_stock['Generico'] = df_stock['Generico'].astype(str).str.strip()
            df_mov['Generico'] = df_mov['Generico'].astype(str).str.strip()
            
            # --- 1. CONSOLIDAR STOCK ACTUAL POR GENÉRICO ---
            df_stock_resumen = df_stock.groupby('Generico').agg({
                'Cant Fraccionado': 'sum'
            }).reset_index()
            
            # --- 2. CONSOLIDAR CONSUMO (MOVIMIENTOS) POR GENÉRICO ---
            df_salidas = df_mov[df_mov['Cantidad'] < 0].copy()
            df_salidas['Cantidad_Positiva'] = df_salidas['Cantidad'].abs()
            
            df_consumo = df_salidas.groupby('Generico')['Cantidad_Positiva'].sum().reset_index()
            df_consumo.columns = ['Generico', 'Consumo_Total_3M']
            
            # --- 3. UNIÓN DE BASES DE DATOS POR GENÉRICO ---
            df_dashboard = pd.merge(df_stock_resumen, df_consumo, on='Generico', how='left').fillna(0)
            
            # --- 4. CÁLCULOS MATEMÁTICOS DE REPOSICIÓN ---
            df_dashboard['Consumo_Promedio_Mensual'] = (df_dashboard['Consumo_Total_3M'] / 3).round(1)
            df_dashboard['Consumo_Diario_Promedio'] = (df_dashboard['Consumo_Promedio_Mensual'] / 30).round(2)
            
            DIAS_PROVEEDOR = 10
            DIAS_SEGURIDAD = 5
            
            df_dashboard['Stock_Crítico'] = (df_dashboard['Consumo_Diario_Promedio'] * DIAS_PROVEEDOR).round(1)
            df_dashboard['Necesidad_Pedido'] = (df_dashboard['Consumo_Diario_Promedio'] * (DIAS_PROVEEDOR + DIAS_SEGURIDAD)).round(1)
            
            df_dashboard['Pedido_Sugerido_1_Mes'] = ((df_dashboard['Consumo_Diario_Promedio'] * 40) - df_dashboard['Cant Fraccionado']).round(1)
            df_dashboard['Pedido_Sugerido_1_Mes'] = df_dashboard['Pedido_Sugerido_1_Mes'].apply(lambda x: x if x > 0 else 0)
            
            # Clasificación de Estado
            def asignar_estado(row):
                if row['Consumo_Promedio_Mensual'] == 0:
                    return '💤 Sin Consumo Reciente'
                elif row['Cant Fraccionado'] <= row['Stock_Crítico']:
                    return '🚨 CRÍTICO (Menos de 10 días de stock)'
                elif row['Cant Fraccionado'] <= row['Necesidad_Pedido']:
                    return '⚠️ SOLICITAR COMPRA (Reponer Stock)'
                return '✅ Óptimo'
                
            df_dashboard['Estado'] = df_dashboard.apply(asignar_estado, axis=1)
            
            # --- PREPARACIÓN DE TABLAS DE ALERTA ---
            df_mail_criticos = df_dashboard[df_dashboard['Estado'].str.contains('🚨')][['Generico', 'Cant Fraccionado', 'Pedido_Sugerido_1_Mes']].rename(columns={'Cant Fraccionado': 'Stock Actual', 'Pedido_Sugerido_1_Mes': 'Pedido Sugerido'})
            df_mail_pedidos = df_dashboard[df_dashboard['Estado'].str.contains('⚠️')][['Generico', 'Cant Fraccionado', 'Pedido_Sugerido_1_Mes']].rename(columns={'Cant Fraccionado': 'Stock Actual', 'Pedido_Sugerido_1_Mes': 'Pedido Sugerido'})
            
            # --- MÓDULO DE EMAIL (BARRA LATERAL) ---
            st.sidebar.header("📧 Módulo de Notificaciones")
            email_destino = st.secrets.get("email_destino", None)
            
            if st.sidebar.button("📨 Enviar Alertas por Mail"):
                if email_destino:
                    with st.spinner("Enviando correo unificado..."):
                        exito = enviar_correo_alerta(email_destino, df_mail_criticos, df_mail_pedidos)
                        if exito:
                            st.sidebar.success("¡Alerta enviada con éxito!")
                        else:
                            st.sidebar.error("Error al enviar.")
                else:
                    st.sidebar.warning("Por favor, ingresa un correo.")
            
            # Métricas generales en pantalla
            cant_criticos = df_dashboard[df_dashboard['Estado'].str.contains('🚨')].shape[0]
            cant_pedido = df_dashboard[df_dashboard['Estado'].str.contains('⚠️')].shape[0]

            
            m1, m2, m3 = st.columns(3)
            m1.metric("🚨 Genéricos en Stock Crítico", cant_criticos)
            m2.metric("⚠️ Con necesidad de pedido", cant_pedido)
            m3.metric("📦 Total Genéricos Evaluados", df_dashboard.shape[0])

            
            st.markdown("---")
            
            # --- NUEVA SECCIÓN DE FILTROS INTERACTIVOS ---
            st.subheader("🔎 Filtros de Visualización")
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                estados_seleccionados = st.multiselect(
                    "Filtrar por Condición de Stock:",
                    options=['🚨 CRÍTICO (Menos de 10 días de stock)', '⚠️ SOLICITAR COMPRA (Reponer Stock)', '✅ Óptimo', '💤 Sin Consumo Reciente'],
                    default=['🚨 CRÍTICO (Menos de 10 días de stock)', '⚠️ SOLICITAR COMPRA (Reponer Stock)']
                )
            with col_f2:
                buscar_medicamento = st.text_input("Buscar medicamento específico por nombre:")

            # Aplicar los filtros al dataframe
            df_filtrado = df_dashboard[df_dashboard['Estado'].isin(estados_seleccionados)]
            if buscar_medicamento:
                df_filtrado = df_filtrado[df_filtrado['Generico'].str.contains(buscar_medicamento, case=False)]
            
            st.subheader("📋 Estado Detallado del Inventario")
            
            # Renombramos columnas para la vista del usuario
            df_vista = df_filtrado[['Generico', 'Cant Fraccionado', 'Consumo_Promedio_Mensual', 'Pedido_Sugerido_1_Mes', 'Estado']].rename(columns={
                'Generico': 'Medicamento (Genérico)',
                'Cant Fraccionado': 'Stock Fraccionado Actual',
                'Consumo_Promedio_Mensual': 'Consumo Prom. Mensual',
                'Pedido_Sugerido_1_Mes': 'Pedido Sugerido (1 Mes)'
            })
            
            st.dataframe(df_vista, width='stretch', hide_index=True)
            
        except Exception as e:
            st.error(f"Error al procesar la información: {e}")
