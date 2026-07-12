import os
import hashlib
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, QFontDialog,
    QColorDialog, QMessageBox, QMenuBar, QMenu, QAction, QInputDialog,
    QLineEdit, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolBar
)
from PyQt5.QtGui import QFont, QIcon, QKeyEvent
from PyQt5.QtCore import QSize

# Clave secreta para el cifrado y hash
CLAVE_SECRETA = b"MiClaveSecretaUltraConfidencial123"

class BlocDeNotas(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ECSV")
        self.setGeometry(100, 100, 900, 650) # Ampliado un poco para acomodar la barra
        self.archivo_actual = None
        self.cambios_pendientes = False

        self.text_edit = QTextEdit()
        self.setCentralWidget(self.text_edit)
        
        self.text_edit.textChanged.connect(self.marcar_modificado)
        
        # Primero creamos las acciones compartidas, luego los menús y la barra de herramientas
        self.crear_acciones()
        self.crear_menus()
        self.crear_barra_herramientas()
        self.aplicar_estilo()

    def crear_acciones(self):
        """Define todas las acciones del programa con sus respectivos iconos."""
        # --- Acciones de Archivo ---
        self.abrir_action = QAction(QIcon(r'\ESCV_0.1\Assets\Open.png'), "Abrir", self)
        self.abrir_action.setStatusTip("Abrir un archivo cifrado")
        self.abrir_action.triggered.connect(self.abrir_archivo)
        
        self.guardar_action = QAction(QIcon(r'\ESCV_0.1\Assets\guardar.png'), "Guardar", self)
        self.guardar_action.setStatusTip("Guardar archivo actual")
        self.guardar_action.triggered.connect(self.guardar_archivo)
        
        self.guardar_como_action = QAction(QIcon(r'\ESCV_0.1\Assets\guardar_como.png'), "Guardar Como", self)
        self.guardar_como_action.setStatusTip("Guardar con nueva extensión")
        self.guardar_como_action.triggered.connect(self.guardar_como)

        # --- Acciones de Formato ---
        self.fuente_action = QAction(QIcon(r'\ESCV_0.1\Assets\fuente.png'), "Fuente", self)
        self.fuente_action.triggered.connect(self.cambiar_fuente)
        
        self.aumentar_tamano_action = QAction(QIcon('mas.png'), "Agrandar", self)
        self.aumentar_tamano_action.triggered.connect(self.aumentar_tamano_texto)
        
        self.disminuir_tamano_action = QAction(QIcon('menos.png'), "Encoger", self)
        self.disminuir_tamano_action.triggered.connect(self.disminuir_tamano_texto)

        # --- Acciones de Insertar / Herramientas / Ayuda ---
        self.imagen_action = QAction(QIcon('imagen.png'), "Imagen", self)
        self.imagen_action.triggered.connect(self.insertar_imagen)

        self.resaltar_action = QAction(QIcon('resaltar.png'), "Resaltar", self)
        self.resaltar_action.triggered.connect(self.resaltar_texto)

        self.ayuda_action = QAction(QIcon('ayuda.png'), "Acerca de", self)
        self.ayuda_action.triggered.connect(self.mostrar_pregunta)

    def crear_menus(self):
        barra_menu = self.menuBar()

        # Menú Archivo
        archivo_menu = barra_menu.addMenu("Archivo")
        archivo_menu.addAction(self.abrir_action)
        archivo_menu.addAction(self.guardar_action)
        archivo_menu.addAction(self.guardar_como_action)

        # Menú Formato
        formato_menu = barra_menu.addMenu("Formato")
        formato_menu.addAction(self.fuente_action)
        formato_menu.addAction(self.aumentar_tamano_action)
        formato_menu.addAction(self.disminuir_tamano_action)

        # Menú Insertar
        insertar_menu = barra_menu.addMenu("Insertar")
        insertar_menu.addAction(self.imagen_action)

        # Menú Herramientas
        herramientas_menu = barra_menu.addMenu("Herramientas")
        herramientas_menu.addAction(self.resaltar_action)

        # Menú Ayuda
        ayuda_menu = barra_menu.addMenu("Ayuda")
        ayuda_menu.addAction(self.ayuda_action)

    def crear_barra_herramientas(self):
        """Crea la barra de herramientas superior con botones e iconos al estilo Wordpad."""
        toolbar = QToolBar("Barra de Herramientas Principal")
        toolbar.setIconSize(QSize(32, 32)) # Tamaño de los botones con imágenes
        self.addToolBar(toolbar)

        # Sección Archivo
        toolbar.addAction(self.abrir_action)
        toolbar.addAction(self.guardar_action)
        toolbar.addAction(self.guardar_como_action)
        
        toolbar.addSeparator() # Línea divisoria vertical

        # Sección Formato de Texto
        toolbar.addAction(self.fuente_action)
        toolbar.addAction(self.aumentar_tamano_action)
        toolbar.addAction(self.disminuir_tamano_action)
        
        toolbar.addSeparator()

        # Sección Inserciones y Extras
        toolbar.addAction(self.imagen_action)
        toolbar.addAction(self.resaltar_action)
        
        toolbar.addSeparator()
        toolbar.addAction(self.ayuda_action)

    def aplicar_estilo(self):
        self.setStyleSheet("""
            QMainWindow {
                background-image: url('textura.jpg');
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
                background-size: cover;
                border: 5px solid #ffa07a;
            }
            QTextEdit {
                background-color: rgba(10, 10, 10, 0.70);
                border: 3px solid #ffa07a;
                border-radius: 10px;
                padding: 15px;
                font-size: 27px;
                color: #fff;
                font-family: Arial;
            }
            QMenuBar {
                background-color: #ffe680;
                border-bottom: 2px solid #f4a460;
                font-family: "Calibri (Body)";
            }
            QMenu {
                background-color: #fffaf0;
                font-family: "Calibri (Body)";
            }
            QToolBar {
                background-color: #f5f5f5;
                border-bottom: 2px solid #dcdcdc;
                padding: 5px;
                spacing: 10px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #b8d6f3;
            }
            QToolButton:pressed {
                background-color: #cce4f7;
                border: 1px solid #99c1e9;
            }
        """)

    def marcar_modificado(self):
        if not self.cambios_pendientes:
            self.setWindowTitle("(*) ECSV")
            self.cambios_pendientes = True

    # ================= MÉTODOS DE SEGURIDAD =================
    def _cifrar_descifrar(self):
        contenido_html = self.text_edit.toHtml().encode('utf-8')
        datos_cifrados = bytearray()
        for i in range(len(contenido_html)):
            datos_cifrados.append(contenido_html[i] ^ CLAVE_SECRETA[i % len(CLAVE_SECRETA)])
        return bytes(datos_cifrados)

    def _descifrar_datos(self, datos_cifrados):
        datos_descifrados = bytearray()
        for i in range(len(datos_cifrados)):
            datos_descifrados.append(datos_cifrados[i] ^ CLAVE_SECRETA[i % len(CLAVE_SECRETA)])
        return datos_descifrados.decode('utf-8')

    # ================= GESTIÓN DE ARCHIVOS =================
    def abrir_archivo(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Archivos ECSV (*.ecs *.*)")
        if archivo:
            try:
                with open(archivo, "rb") as f:
                    todo_el_archivo = f.read()
                
                if len(todo_el_archivo) < 32:
                    raise ValueError("Archivo demasiado corto o corrupto.")
                
                datos_cifrados = todo_el_archivo[:-32]
                firma_guardada = todo_el_archivo[-32:]
                
                firma_real = hashlib.sha256(datos_cifrados + CLAVE_SECRETA).digest()
                
                if firma_guardada != firma_real:
                    QMessageBox.critical(self, "Error de Integridad", "¡EL ARCHIVO HA SIDO MODIFICADO FUERA DE ESTE PROGRAMA Y ESTÁ CORRUPTO!")
                    return

                contenido_html = self._descifrar_datos(datos_cifrados)
                self.text_edit.setHtml(contenido_html)
                self.archivo_actual = archivo
                self.cambios_pendientes = False
                self.setWindowTitle(f"ECSV - {os.path.basename(archivo)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo de forma segura. Detalle: {e}")

    def guardar_archivo(self):
        if self.archivo_actual:
            try:
                datos_cifrados = self._cifrar_descifrar()
                firma = hashlib.sha256(datos_cifrados + CLAVE_SECRETA).digest()
                
                with open(self.archivo_actual, "wb") as f:
                    f.write(datos_cifrados + firma)
                    
                self.cambios_pendientes = False
                self.setWindowTitle(f"ECSV - {os.path.basename(self.archivo_actual)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar: {e}")
        else:
            self.guardar_como()

    def guardar_como(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Guardar Como - Seleccionar Extensión")
        layout = QVBoxLayout()

        lbl_ext = QLabel("Elige una extensión de exactamente 3 caracteres (ej: ecs, sec, top):")
        txt_ext = QLineEdit("ecs")
        txt_ext.setMaxLength(3)

        btn_guardar = QPushButton("Continuar")
        
        layout.addWidget(lbl_ext)
        layout.addWidget(txt_ext)
        layout.addWidget(btn_guardar)
        dialogo.setLayout(layout)

        def procesar_guardado():
            ext = txt_ext.text().strip().lower()
            if len(ext) != 3 or not ext.isalnum():
                QMessageBox.warning(dialogo, "Extensión Inválida", "La extensión debe tener exactamente 3 caracteres alfanuméricos.")
                return
            dialogo.accept()

        btn_guardar.clicked.connect(procesar_guardado)
        
        if dialogo.exec_() == QDialog.Accepted:
            extension_elegida = txt_ext.text().strip().lower()
            filtro = f"Archivo Personalizado (*.{extension_elegida})"
            
            archivo, _ = QFileDialog.getSaveFileName(self, "Save File", "", filtro)
            if archivo:
                if not archivo.lower().endswith(f".{extension_elegida}"):
                    archivo += f".{extension_elegida}"
                
                self.archivo_actual = archivo
                self.guardar_archivo()

    # ================= OTROS MÉTODOS =================
    def cambiar_fuente(self):
        fuente, ok = QFontDialog.getFont(self.text_edit.currentFont(), self)
        if ok:
            self.text_edit.setCurrentFont(fuente)

    def aumentar_tamano_texto(self):
        # Obtenemos el formato del cursor actual
        cursor = self.text_edit.textCursor()
        formato = cursor.charFormat()
        
        # Obtenemos el tamaño actual en puntos. Si es 0 (no definido), usamos 27 (el tamaño de tu CSS)
        tamano_actual = formato.fontPointSize()
        if tamano_actual <= 0:
            tamano_actual = 27
            
        # Calculamos el nuevo tamaño (Máximo 72)
        nuevo_tamano = min(tamano_actual + 2, 72)
        
        # Aplicamos el nuevo tamaño al formato y luego al cursor
        formato.setFontPointSize(nuevo_tamano)
        cursor.setCharFormat(formato)
        self.text_edit.setTextCursor(cursor)
        self.marcar_modificado()

    def disminuir_tamano_texto(self):
        # Obtenemos el formato del cursor actual
        cursor = self.text_edit.textCursor()
        formato = cursor.charFormat()
        
        # Obtenemos el tamaño actual en puntos. Si es 0, usamos 27
        tamano_actual = formato.fontPointSize()
        if tamano_actual <= 0:
            tamano_actual = 27
            
        # Calculamos el nuevo tamaño (Mínimo 6)
        nuevo_tamano = max(tamano_actual - 2, 6)
        
        # Aplicamos el nuevo tamaño al formato y luego al cursor
        formato.setFontPointSize(nuevo_tamano)
        cursor.setCharFormat(formato)
        self.text_edit.setTextCursor(cursor)
        self.marcar_modificado()

    def insertar_imagen(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Insert Images", "", "Images (*.png *.jpg *.jpeg *.gif)")
        if archivo:
            ancho, ok = QInputDialog.getInt(self, "Image Scale", "¿Ancho en píxeles?", 200, 50, 1000)
            if ok:
                cursor = self.text_edit.textCursor()
                cursor.insertHtml(f'<img src="{archivo}" width="{ancho}">')
                self.marcar_modificado()

    def resaltar_texto(self):
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.text_edit.textCursor()
            formato = cursor.charFormat()
            formato.setBackground(color)
            cursor.mergeCharFormat(formato)
            self.marcar_modificado()

    def mostrar_pregunta(self):
        QMessageBox.information(self, "Version ", ("Endry Cumare Script Veiwer (0.0.1 P)") )

    def obtener_fuente_actual(self):
        return self.text_edit.currentFont().family()

if __name__ == "__main__":
    app = QApplication([])
    ventana = BlocDeNotas()
    ventana.show()
    app.exec_()