# 📦 Sistema de Control de Stock y Reorden de Insumos

Esta aplicación te permite procesar de forma automática y rápida los archivos Excel de **Stock Actual** y **Movimientos Trimestrales** exportados desde tu sistema, calculando los niveles críticos, puntos de reorden y generando la lista de pedidos necesarios sin realizar ningún cálculo manual.

---

## 🛠️ Requisitos Previos (Solo se hace una vez)

Antes de comenzar, asegúrate de tener instalado **Python** en la computadora.

### 1. Verificar o instalar Python
1. Descarga Python desde el sitio oficial: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. **MUY IMPORTANTE AL INSTALAR:** En la primera pantalla del instalador, marca la casilla que dice **"Add Python to PATH"** (o "Agregar Python al PATH").
3. Haz clic en **Install Now** y completa la instalación.

---

## 🚀 Configuración Inicial Paso a Paso

Sigue estos sencillos pasos para dejar lista la aplicación en tu computadora:

### En Windows:

1. **Abrir la terminal en la carpeta del proyecto:**
   * Abre la carpeta donde guardaste este programa.
   * Haz clic en la barra de direcciones de la carpeta (donde se ve la ruta de las carpetas).
   * Escribe `cmd` y presiona la tecla **Enter**. Se abrirá una ventana negra (Símbolo del sistema).

2. **Crear el entorno virtual:**
   Copia y pega el siguiente comando en la ventana negra y presiona **Enter**:

   python -m venv venv

   *(Verás que se crea una nueva carpeta llamada `venv` dentro del proyecto).*

3. **Activar el entorno virtual:**
   Escribe el siguiente comando y presiona **Enter**:

   venv\Scripts\activate

   *(Sabrás que funcionó porque al principio de la línea aparecerá el texto `(venv)`).*

4. **Instalar las herramientas necesarias:**
   Copia y pega este comando y presiona **Enter**:
   
   pip install -r requirements.txt
   
   *(Espera un momento a que terminen de descargarse las librerías necesarias).*

---

### En Mac (macOS):

1. Abre la aplicación **Terminal**.
2. Arrastra la carpeta del proyecto dentro de la ventana de la Terminal y escribe `cd ` antes de la ruta (o navega hasta la carpeta).
3. Ejecuta los siguientes comandos uno por uno:
   
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt


---

## 💻 Cómo Usar la Aplicación Día a Día

Cada vez que quieras abrir el programa para analizar tus inventarios:

1. Abre la terminal en la carpeta del proyecto (escribiendo `cmd` en la barra de direcciones de la carpeta).
2. Activa el entorno virtual escribiendo:
   * **Windows:** `venv\Scripts\activate`
   * **Mac:** `source venv/bin/activate`
3. Inicia la aplicación con este comando:
   
   streamlit run app.py

4. Se abrirá automáticamente una ventana en tu navegador web (Google Chrome, Edge, etc.) con el panel del sistema.

---

## 📑 Pasos para Usar el Panel Web

1. **Subir archivos:** 
   * En el botón **1. Subir Planilla de Stock Actual**, selecciona o arrastra la planilla de stock exportada de tu sistema.
   * En el botón **2. Subir Planilla de Movimientos Trimestrales**, selecciona o arrastra la planilla de salidas/consumos.
2. **Ajustar Parámetros (Opcional):** En la barra lateral izquierda puedes modificar el *Tiempo de Entrega del Proveedor* y el *Stock de Seguridad*.
3. **Revisar Alertas:** El tablero mostrará en rojo los productos **CRÍTICOS** (pedido urgente) y en amarillo los que están en **REORDEN**.
4. **Descargar Orden de Compra:** Al final de la página encontrarás el botón **"Descargar Solicitud de Pedidos en Excel"** para guardar el reporte filtrado y listo para enviar a compras.

---

## 🛑 Cómo Cerrar el Programa

Cuando termines de usar la aplicación:
1. Ve a la ventana negra de la terminal.
2. Presiona las teclas **Ctrl + C** en tu teclado para detener el servidor.
3. Cierra la ventana.