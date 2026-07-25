"""
CDV - Confidential Document Viewer
Editor de Texto Seguro con cifrado y sistema de deshacer/rehacer
Versión 0.0.2P - Modo Oscuro Completo
"""
import os
import sys
import hashlib
import base64
import configparser
from pathlib import Path
import random

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, QFontDialog,
    QColorDialog, QMessageBox, QMenuBar, QMenu, QAction, QInputDialog,
    QLineEdit, QToolBar, QLabel, QStatusBar, QDialog, QVBoxLayout,
    QHBoxLayout, QPushButton, QCheckBox
)
from PyQt5.QtGui import QFont, QIcon, QKeySequence, QColor, QTextCursor
from PyQt5.QtCore import QSize, Qt, QObject, pyqtSignal

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("ADVERTENCIA: Verifica si esta instalado cryptography. Estás usando el cifrado XOR básico.")


# ==================== DIÁLOGO DE CONTRASEÑA ====================

class PasswordDialog(QDialog):

    
    def __init__(self, titulo, mensaje, modo_guardar=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.modo_guardar = modo_guardar
        self.contrasena = ""
        self.setup_ui(mensaje)
        self.aplicar_estilo_oscuro()
    
    def setup_ui(self, mensaje):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Mensaje
        self.label = QLabel(mensaje)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 12px; color: #ffffff;")
        layout.addWidget(self.label)
        
        # Campo de contraseña
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Ingresa la contraseña...")
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4a6a8a;
            }
        """)
        layout.addWidget(self.password_input)
        
        # Checkbox para mostrar contraseña
        self.mostrar_check = QCheckBox("Mostrar contraseña")
        self.mostrar_check.setStyleSheet("color: #aaaaaa;")
        self.mostrar_check.toggled.connect(self.toggle_mostrar_contrasena)
        layout.addWidget(self.mostrar_check)
        
        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)
        
        self.btn_aceptar = QPushButton("Aceptar")
        self.btn_aceptar.clicked.connect(self.aceptar)
        self.btn_aceptar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        
        botones_layout.addWidget(self.btn_aceptar)
        botones_layout.addWidget(self.btn_cancelar)
        layout.addLayout(botones_layout)
        
        self.setLayout(layout)
        
        # Conectar Enter para aceptar
        self.password_input.returnPressed.connect(self.aceptar)
    
    def toggle_mostrar_contrasena(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def aceptar(self):
        contrasena = self.password_input.text()
        if self.modo_guardar and len(contrasena) < 4:
            QMessageBox.warning(self, "Contraseña corta", 
                "La contraseña debe tener al menos 4 caracteres.")
            return
        if not contrasena:
            QMessageBox.warning(self, "Contraseña vacía", 
                "Debes ingresar una contraseña.")
            return
        self.contrasena = contrasena
        self.accept()
    
    def get_contrasena(self):
        return self.contrasena
    
    def aplicar_estilo_oscuro(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
            }
            QLabel {
                color: #ffffff;
            }
        """)


# ==================== CONFIGURACIÓN ====================

class Configuracion:
    """Gestor de configuración de la aplicación"""
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.ruta_config = Path("config/settings.ini")
        self.cargar_o_crear()
    
    def cargar_o_crear(self):
        if self.ruta_config.exists():
            self.config.read(self.ruta_config)
        else:
            self.crear_predeterminada()
    
    def crear_predeterminada(self):
        self.config['Editor'] = {
            'fuente': 'Arial',
            'tamano_fuente': '27',
            'color_fondo': '#1a1a1a',
            'color_texto': '#ffffff',
            'max_historial': '50'
        }
        self.config['Seguridad'] = {
            'algoritmo': 'aes'
        }
        self.config['Ventana'] = {
            'ancho': '1000',
            'alto': '700',
            'maximizada': 'False'
        }
        self.config['Formatos'] = {
            'extensiones': 'cdv,sec,enc,docx,html,htm,txt'
        }
        self.guardar()
    
    def guardar(self):
        os.makedirs(self.ruta_config.parent, exist_ok=True)
        with open(self.ruta_config, 'w') as f:
            self.config.write(f)
    
    def obtener(self, seccion, clave, valor_predeterminado=''):
        try:
            return self.config.get(seccion, clave)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return valor_predeterminado
    
    def establecer(self, seccion, clave, valor):
        if not self.config.has_section(seccion):
            self.config.add_section(seccion)
        self.config.set(seccion, clave, str(valor))
        self.guardar()


# ==================== SEGURIDAD CON CONTRASEÑA ====================

class Seguridad:
    """Maneja el cifrado y descifrado de archivos con contraseña"""
    
    def __init__(self, config):
        self.config = config
    
    def _derivar_clave(self, contrasena, salt=None):
        """Deriva una clave a partir de la contraseña y un salt"""
        if salt is None:
            salt = b"E"
        
        if CRYPTOGRAPHY_AVAILABLE:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=200000,
            )
            clave = kdf.derive(contrasena.encode('utf-8'))
            return base64.urlsafe_b64encode(clave)
        else:
            clave = hashlib.sha256(salt + contrasena.encode('utf-8')).digest()
            return base64.urlsafe_b64encode(clave)
    
    def cifrar_con_contrasena(self, contenido_html, contrasena):
        """Cifra el contenido usando una contraseña"""
        datos = contenido_html.encode('utf-8')
        
        # Generar salt aleatorio
        salt = hashlib.sha256(str(random.random()).encode()).digest()[:16]
        
        if CRYPTOGRAPHY_AVAILABLE:
            try:
                clave = self._derivar_clave(contrasena, salt)
                f = Fernet(clave)
                datos_cifrados = f.encrypt(datos)
            except Exception as e:
                print(f"Error en cifrado AES: {e}, usando XOR")
                datos_cifrados = self._cifrar_xor(datos, contrasena)
        else:
            datos_cifrados = self._cifrar_xor(datos, contrasena)
        
        # Guardar salt + datos cifrados
        return salt + datos_cifrados
    
    def descifrar_con_contrasena(self, datos_completos, contrasena):
        """Descifra el contenido usando una contraseña"""
        salt = datos_completos[:16]
        datos_cifrados = datos_completos[16:]
        
        if CRYPTOGRAPHY_AVAILABLE:
            try:
                clave = self._derivar_clave(contrasena, salt)
                f = Fernet(clave)
                datos_descifrados = f.decrypt(datos_cifrados)
                return datos_descifrados.decode('utf-8')
            except Exception as e:
                print(f"Error en descifrado AES: {e}")
                raise ValueError("Contraseña incorrecta o archivo corrupto")
        else:
            try:
                return self._descifrar_xor(datos_cifrados, contrasena)
            except:
                raise ValueError("Contraseña incorrecta o archivo corrupto")
    
    def _cifrar_xor(self, datos, contrasena):
        """Cifrado XOR simple con contraseña (fallback)"""
        clave = contrasena.encode('utf-8')
        datos_cifrados = bytearray()
        for i in range(len(datos)):
            datos_cifrados.append(datos[i] ^ clave[i % len(clave)])
        return bytes(datos_cifrados)
    
    def _descifrar_xor(self, datos_cifrados, contrasena):
        """Descifrado XOR simple con contraseña (fallback)"""
        clave = contrasena.encode('utf-8')
        datos_descifrados = bytearray()
        for i in range(len(datos_cifrados)):
            datos_descifrados.append(datos_cifrados[i] ^ clave[i % len(clave)])
        return datos_descifrados.decode('utf-8', errors='ignore')
    
    def generar_firma(self, datos_completos, contrasena):
        """Genera la firma de integridad con la contraseña"""
        return hashlib.sha256(datos_completos + contrasena.encode('utf-8')).digest()
    
    def verificar_firma(self, datos_completos, firma_guardada, contrasena):
        """Verifica la integridad del archivo"""
        firma_calculada = self.generar_firma(datos_completos, contrasena)
        return firma_calculada == firma_guardada


# ==================== HISTORIAL ====================

class HistorialManager(QObject):
    estado_cambiado = pyqtSignal(bool)
    
    def __init__(self, max_historial=50):
        super().__init__()
        self.historial = []
        self.indice_actual = -1
        self.max_historial = max_historial
        self._cambios_pendientes = False
        self._bloqueado = False
    
    def guardar_estado(self, contenido_html):
        if self._bloqueado:
            return
        
        if self.indice_actual < len(self.historial) - 1:
            self.historial = self.historial[:self.indice_actual + 1]
        
        if self.historial and self.historial[-1] == contenido_html:
            return
        
        self.historial.append(contenido_html)
        
        if len(self.historial) > self.max_historial:
            self.historial.pop(0)
            self.indice_actual = len(self.historial) - 1
        else:
            self.indice_actual = len(self.historial) - 1
        
        self._cambios_pendientes = True
        self.estado_cambiado.emit(True)
    
    def deshacer(self):
        if self.indice_actual > 0:
            self._bloqueado = True
            self.indice_actual -= 1
            self._cambios_pendientes = False
            self.estado_cambiado.emit(False)
            self._bloqueado = False
            return self.historial[self.indice_actual]
        return None
    
    def rehacer(self):
        if self.indice_actual < len(self.historial) - 1:
            self._bloqueado = True
            self.indice_actual += 1
            self._cambios_pendientes = self.indice_actual == len(self.historial) - 1
            self.estado_cambiado.emit(self._cambios_pendientes)
            self._bloqueado = False
            return self.historial[self.indice_actual]
        return None
    
    def limpiar(self):
        self.historial = []
        self.indice_actual = -1
        self._cambios_pendientes = False
        self.estado_cambiado.emit(False)
    
    def hay_cambios_pendientes(self):
        return self._cambios_pendientes
    
    def hay_deshacer(self):
        return self.indice_actual > 0
    
    def hay_rehacer(self):
        return self.indice_actual < len(self.historial) - 1


# ==================== EDITOR PRINCIPAL ====================

class CDVEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.config = Configuracion()
        self.seguridad = Seguridad(self.config)
        self.archivo_actual = None
        self.archivo_cifrado = False
        self.contrasena_archivo = None
        self.tamano_fuente_base = int(self.config.obtener('Editor', 'tamano_fuente', '27'))
        
        self.init_ui()
        
        max_hist = int(self.config.obtener('Editor', 'max_historial', '50'))
        self.historial = HistorialManager(max_historial=max_hist)
        self.historial.estado_cambiado.connect(self.actualizar_titulo)
        
        self.mostrar_bienvenida()
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.aplicar_configuracion_inicial()
    
    def init_ui(self):
        ancho = int(self.config.obtener('Ventana', 'ancho', '1000'))
        alto = int(self.config.obtener('Ventana', 'alto', '700'))
        
        self.setWindowTitle("CDV - Confidential Document Viewer")
        self.setGeometry(100, 100, ancho, alto)
        
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.setCentralWidget(self.text_edit)
        
        self.crear_acciones()
        self.crear_menus()
        self.crear_barra_herramientas()
        self.crear_barra_estado()
        self.configurar_atajos_teclado()
        self.aplicar_estilo_oscuro()
    
    def crear_acciones(self):
        # Archivo
        self.nuevo_action = QAction("Nuevo (Ctrl+N)", self)
        self.nuevo_action.setShortcut(QKeySequence("Ctrl+N"))
        self.nuevo_action.triggered.connect(self.nuevo_archivo)
        
        self.abrir_action = QAction("Abrir (Ctrl+O)", self)
        self.abrir_action.setShortcut(QKeySequence("Ctrl+O"))
        self.abrir_action.triggered.connect(self.abrir_archivo)
        
        self.guardar_action = QAction("Guardar (Ctrl+S)", self)
        self.guardar_action.setShortcut(QKeySequence("Ctrl+S"))
        self.guardar_action.triggered.connect(self.guardar_archivo)
        
        self.guardar_como_action = QAction("Guardar Como (Ctrl+Shift+S)", self)
        self.guardar_como_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.guardar_como_action.triggered.connect(self.guardar_como)
        
        # Edición
        self.deshacer_action = QAction("Deshacer (Ctrl+Z)", self)
        self.deshacer_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.deshacer_action.triggered.connect(self.deshacer)
        self.deshacer_action.setEnabled(False)
        
        self.rehacer_action = QAction("Rehacer (Ctrl+Y)", self)
        self.rehacer_action.setShortcut(QKeySequence("Ctrl+Y"))
        self.rehacer_action.triggered.connect(self.rehacer)
        self.rehacer_action.setEnabled(False)
        
        # Formato
        self.fuente_action = QAction("Fuente", self)
        self.fuente_action.triggered.connect(self.cambiar_fuente)
        
        self.aumentar_tamano_action = QAction("Agrandar", self)
        self.aumentar_tamano_action.triggered.connect(self.aumentar_tamano)
        
        self.disminuir_tamano_action = QAction("Encoger", self)
        self.disminuir_tamano_action.triggered.connect(self.disminuir_tamano)
        
        # Insertar
        self.imagen_action = QAction("Insertar Imagen", self)
        self.imagen_action.triggered.connect(self.insertar_imagen)
        
        self.resaltar_action = QAction("Resaltar Texto", self)
        self.resaltar_action.triggered.connect(self.resaltar_texto)
        
        self.ayuda_action = QAction("Acerca de CDV", self)
        self.ayuda_action.triggered.connect(self.mostrar_acerca_de)
    
    def crear_menus(self):
        barra_menu = self.menuBar()
        barra_menu.setStyleSheet("""
            QMenuBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border-bottom: 1px solid #3d3d3d;
                font-family: "Segoe UI";
                font-size: 11px;
            }
            QMenuBar::item {
                padding: 5px 10px;
                background-color: transparent;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)
        
        archivo_menu = barra_menu.addMenu("Archivo")
        archivo_menu.addAction(self.nuevo_action)
        archivo_menu.addSeparator()
        archivo_menu.addAction(self.abrir_action)
        archivo_menu.addAction(self.guardar_action)
        archivo_menu.addAction(self.guardar_como_action)
        
        edicion_menu = barra_menu.addMenu("Edición")
        edicion_menu.addAction(self.deshacer_action)
        edicion_menu.addAction(self.rehacer_action)
        
        formato_menu = barra_menu.addMenu("Formato")
        formato_menu.addAction(self.fuente_action)
        formato_menu.addAction(self.aumentar_tamano_action)
        formato_menu.addAction(self.disminuir_tamano_action)
        
        insertar_menu = barra_menu.addMenu("Insertar")
        insertar_menu.addAction(self.imagen_action)
        
        herramientas_menu = barra_menu.addMenu("Herramientas")
        herramientas_menu.addAction(self.resaltar_action)
        herramientas_menu.addSeparator()
        
        cambiar_clave_action = QAction("Cambiar Clave Secreta", self)
        cambiar_clave_action.triggered.connect(self.cambiar_clave)
        herramientas_menu.addAction(cambiar_clave_action)
        
        ayuda_menu = barra_menu.addMenu("Ayuda")
        ayuda_menu.addAction(self.ayuda_action)
    
    def crear_barra_herramientas(self):
        toolbar = QToolBar("Barra de Herramientas Principal")
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2d2d2d;
                border: none;
                border-bottom: 1px solid #3d3d3d;
                padding: 4px;
                spacing: 4px;
            }
            QToolButton {
                background-color: transparent;
                color: #ffffff;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 4px 8px;
                font-family: "Segoe UI";
                font-size: 11px;
            }
            QToolButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
            }
            QToolButton:pressed {
                background-color: #4d4d4d;
            }
            QToolButton:disabled {
                color: #666666;
            }
            QToolBar::separator {
                width: 1px;
                background-color: #3d3d3d;
                margin: 4px 8px;
            }
        """)
        
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.nuevo_action)
        toolbar.addAction(self.abrir_action)
        toolbar.addAction(self.guardar_action)
        toolbar.addAction(self.guardar_como_action)
        toolbar.addSeparator()
        toolbar.addAction(self.deshacer_action)
        toolbar.addAction(self.rehacer_action)
        toolbar.addSeparator()
        toolbar.addAction(self.fuente_action)
        toolbar.addAction(self.aumentar_tamano_action)
        toolbar.addAction(self.disminuir_tamano_action)
        toolbar.addSeparator()
        toolbar.addAction(self.imagen_action)
        toolbar.addAction(self.resaltar_action)
        toolbar.addSeparator()
        toolbar.addAction(self.ayuda_action)
    
    def crear_barra_estado(self):
        self.barra_estado = QStatusBar()
        self.barra_estado.setStyleSheet("""
            QStatusBar {
                background-color: #2d2d2d;
                color: #aaaaaa;
                border-top: 1px solid #3d3d3d;
                padding: 2px 8px;
                font-size: 10px;
            }
        """)
        self.setStatusBar(self.barra_estado)
        
        self.posicion_label = QLabel("Línea: 1, Columna: 1")
        self.barra_estado.addWidget(self.posicion_label)
        
        separador = QLabel(" | ")
        separador.setStyleSheet("color: #555555;")
        self.barra_estado.addWidget(separador)
        
        self.archivo_label = QLabel("Sin archivo")
        self.barra_estado.addWidget(self.archivo_label)
        
        separador2 = QLabel(" | ")
        separador2.setStyleSheet("color: #555555;")
        self.barra_estado.addWidget(separador2)
        
        self.estado_label = QLabel("🔓 Sin cifrar")
        self.barra_estado.addWidget(self.estado_label)
        
        self.text_edit.cursorPositionChanged.connect(self.actualizar_posicion)
    
    def configurar_atajos_teclado(self):
        atajos = {
            "Ctrl+W": self.cerrar_archivo,
            "Ctrl+F": self.buscar_texto,
        }
        for atajo, funcion in atajos.items():
            accion = QAction(self)
            accion.setShortcut(QKeySequence(atajo))
            accion.triggered.connect(funcion)
            self.addAction(accion)
    
    def aplicar_estilo_oscuro(self):
        color_fondo = self.config.obtener('Editor', 'color_fondo', '#1a1a1a')
        color_texto = self.config.obtener('Editor', 'color_texto', '#ffffff')
        tamano_fuente = self.config.obtener('Editor', 'tamano_fuente', '27')
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #1a1a1a;
                border: 2px solid #3d3d3d;
            }}
            QTextEdit {{
                background-color: {color_fondo};
                border: 2px solid #3d3d3d;
                border-radius: 6px;
                padding: 15px;
                font-size: {tamano_fuente}px;
                color: {color_texto};
                font-family: Arial;
                selection-background-color: #3d3d3d;
                selection-color: #ffffff;
            }}
            QTextEdit:focus {{
                border: 2px solid #4a6a8a;
            }}
            QScrollBar:vertical {{
                background-color: #1a1a1a;
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #3d3d3d;
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #4d4d4d;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar:horizontal {{
                background-color: #1a1a1a;
                height: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #3d3d3d;
                min-width: 20px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: #4d4d4d;
            }}
            QMessageBox {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QMessageBox QPushButton {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #4d4d4d;
                border-radius: 3px;
                padding: 5px 15px;
                min-width: 60px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #4d4d4d;
            }}
            QInputDialog {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QInputDialog QLineEdit {{
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 4px;
            }}
            QInputDialog QPushButton {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #4d4d4d;
                border-radius: 3px;
                padding: 5px 15px;
            }}
            QInputDialog QPushButton:hover {{
                background-color: #4d4d4d;
            }}
            QFileDialog {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QFileDialog QListView {{
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }}
            QFileDialog QTreeView {{
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }}
            QFileDialog QLineEdit {{
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 4px;
            }}
            QFileDialog QPushButton {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #4d4d4d;
                border-radius: 3px;
                padding: 5px 15px;
            }}
            QFileDialog QPushButton:hover {{
                background-color: #4d4d4d;
            }}
            QFontDialog {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QFontDialog QPushButton {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #4d4d4d;
                border-radius: 3px;
                padding: 5px 15px;
            }}
            QFontDialog QPushButton:hover {{
                background-color: #4d4d4d;
            }}
            QColorDialog {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QColorDialog QPushButton {{
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #4d4d4d;
                border-radius: 3px;
                padding: 5px 15px;
            }}
            QColorDialog QPushButton:hover {{
                background-color: #4d4d4d;
            }}
            QDialog {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QLabel {{
                color: #ffffff;
            }}
        """)
    
    def aplicar_configuracion_inicial(self):
        fuente_nombre = self.config.obtener('Editor', 'fuente', 'Arial')
        tamano = int(self.config.obtener('Editor', 'tamano_fuente', '27'))
        fuente = QFont(fuente_nombre, tamano)
        self.text_edit.setFont(fuente)
        self.tamano_fuente_base = tamano
    
    def actualizar_posicion(self):
        cursor = self.text_edit.textCursor()
        linea = cursor.blockNumber() + 1
        columna = cursor.columnNumber() + 1
        self.posicion_label.setText(f"Línea: {linea}, Columna: {columna}")
    
    def on_text_changed(self):
        if not self.text_edit.isReadOnly():
            contenido = self.text_edit.toHtml()
            self.historial.guardar_estado(contenido)
            self.actualizar_acciones_edicion()
    
    def deshacer(self):
        estado_anterior = self.historial.deshacer()
        if estado_anterior is not None:
            self.text_edit.textChanged.disconnect(self.on_text_changed)
            self.text_edit.setHtml(estado_anterior)
            self.text_edit.textChanged.connect(self.on_text_changed)
            self.actualizar_acciones_edicion()
    
    def rehacer(self):
        estado_siguiente = self.historial.rehacer()
        if estado_siguiente is not None:
            self.text_edit.textChanged.disconnect(self.on_text_changed)
            self.text_edit.setHtml(estado_siguiente)
            self.text_edit.textChanged.connect(self.on_text_changed)
            self.actualizar_acciones_edicion()
    
    def actualizar_acciones_edicion(self):
        self.deshacer_action.setEnabled(self.historial.hay_deshacer())
        self.rehacer_action.setEnabled(self.historial.hay_rehacer())
    
    def actualizar_titulo(self, cambios_pendientes):
        nombre_archivo = os.path.basename(self.archivo_actual) if self.archivo_actual else "Nuevo"
        if cambios_pendientes:
            self.setWindowTitle(f"* CDV - {nombre_archivo}")
        else:
            self.setWindowTitle(f"CDV - {nombre_archivo}")
    
    def actualizar_barra_estado(self):
        if self.archivo_actual:
            self.archivo_label.setText(f"Archivo: {os.path.basename(self.archivo_actual)}")
            if self.archivo_cifrado:
                self.estado_label.setText("Cifrado")
            else:
                self.estado_label.setText("Sin cifrar")
        else:
            self.archivo_label.setText("Sin archivo")
            self.estado_label.setText("Sin cifrar")
    
    def nuevo_archivo(self):
        if self.historial.hay_cambios_pendientes():
            respuesta = QMessageBox.question(
                self, "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Deseas guardarlos?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if respuesta == QMessageBox.Cancel:
                return
            elif respuesta == QMessageBox.Yes:
                self.guardar_archivo()
        
        self.archivo_actual = None
        self.archivo_cifrado = False
        self.contrasena_archivo = None
        self.text_edit.clear()
        self.text_edit.setHtml('<p style="font-size: 27px; color: #ffffff;">Nuevo documento...</p>')
        self.setWindowTitle("CDV - Nuevo Documento")
        self.historial.limpiar()
        self.historial.guardar_estado(self.text_edit.toHtml())
        self.actualizar_acciones_edicion()
        self.actualizar_barra_estado()
    
    def abrir_archivo(self):
        # Obtener extensiones disponibles
        extensiones = self.config.obtener('Formatos', 'extensiones', 'cdv,sec,enc,docx,html,htm,txt')
        ext_list = extensiones.split(',')
        filtro = f"Archivos CDV (*.{' *.'.join(ext_list)})"
        
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Abrir Archivo", "",
            f"{filtro};;Todos los archivos (*.*)"
        )
        if not archivo:
            return
        
        try:
            # Pedir contraseña
            dialog = PasswordDialog(
                "Contraseña requerida",
                f"El archivo '{os.path.basename(archivo)}' está cifrado.\n"
                "Ingresa la contraseña para desbloquearlo:",
                modo_guardar=False,
                parent=self
            )
            
            if dialog.exec_() != QDialog.Accepted:
                return
            
            contrasena = dialog.get_contrasena()
            
            with open(archivo, "rb") as f:
                # Leer el encabezado
                header = f.readline()
                if not header.startswith(b'CDV|'):
                    raise ValueError("Formato de archivo no válido")
                
                # Leer el resto del archivo
                resto = f.read()
                
                if len(resto) < 48:  # Salt (16) + firma (32)
                    raise ValueError("Archivo corrupto o incompleto")
                
                # Los primeros 16 bytes son el salt
                salt = resto[:16]
                datos_con_salt = resto[:-32]  # Todo menos la firma
                firma_guardada = resto[-32:]
                
                # Verificar integridad
                if not self.seguridad.verificar_firma(datos_con_salt, firma_guardada, contrasena):
                    QMessageBox.critical(self, "Error de Integridad",
                                       "Error 0001 - Contraseña incorrecta o el archivo está corrupto")
                    return
                
                # Descifrar contenido
                contenido_html = self.seguridad.descifrar_con_contrasena(datos_con_salt, contrasena)
                
                self.text_edit.textChanged.disconnect(self.on_text_changed)
                self.text_edit.setHtml(contenido_html)
                self.text_edit.textChanged.connect(self.on_text_changed)
                
                self.archivo_actual = archivo
                self.archivo_cifrado = True
                self.contrasena_archivo = contrasena
                self.setWindowTitle(f"CDV - {os.path.basename(archivo)}")
                
                self.historial.limpiar()
                self.historial.guardar_estado(contenido_html)
                self.actualizar_acciones_edicion()
                self.actualizar_barra_estado()
                
                QMessageBox.information(self, "Éxito", 
                    f"Archivo '{os.path.basename(archivo)}' abierto correctamente.")
                
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Error al abrir el archivo:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{e}")
    
    def guardar_archivo(self):
        if not self.archivo_actual:
            self.guardar_como()
            return
        
        try:
            # Si ya tiene contraseña guardada, usarla
            if self.contrasena_archivo:
                contrasena = self.contrasena_archivo
            else:
                # Pedir nueva contraseña
                dialog = PasswordDialog(
                    "Establecer contraseña",
                    f"El archivo '{os.path.basename(self.archivo_actual)}' será cifrado.\n"
                    "Ingresa una contraseña (mínimo 4 caracteres):",
                    modo_guardar=True,
                    parent=self
                )
                
                if dialog.exec_() != QDialog.Accepted:
                    return
                
                contrasena = dialog.get_contrasena()
                self.contrasena_archivo = contrasena
            
            contenido_html = self.text_edit.toHtml()
            
            # Cifrar con contraseña
            datos_con_salt = self.seguridad.cifrar_con_contrasena(contenido_html, contrasena)
            
            # Generar firma
            firma = self.seguridad.generar_firma(datos_con_salt, contrasena)
            
            with open(self.archivo_actual, "wb") as f:
                # Escribir encabezado
                extension = os.path.splitext(self.archivo_actual)[1][1:] or 'cdv'
                f.write(f"CDV|{extension}|{len(datos_con_salt)}\n".encode('utf-8'))
                f.write(datos_con_salt + firma)
            
            self.archivo_cifrado = True
            self.setWindowTitle(f"CDV - {os.path.basename(self.archivo_actual)}")
            self.historial._cambios_pendientes = False
            self.actualizar_titulo(False)
            self.actualizar_barra_estado()
            
            QMessageBox.information(self, "Éxito", 
                f"Archivo guardado correctamente con contraseña.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar:\n{e}")
    
    def guardar_como(self):
        # Obtener extensiones disponibles
        extensiones = self.config.obtener('Formatos', 'extensiones', 'cdv,sec,enc')
        ext_list = [e.strip() for e in extensiones.split(',')]
        
        # Crear filtro para el diálogo
        filtro = []
        for ext in ext_list:
            filtro.append(f"Archivo .{ext} (*.{ext})")
        filtro_str = ";;".join(filtro)
        
        # Mostrar diálogo
        archivo, selected_filter = QFileDialog.getSaveFileName(
            self, "Guardar Como", "",
            f"{filtro_str};;Todos los archivos (*.*)"
        )
        
        if not archivo:
            return
        
        # Verificar si tiene extensión
        extension_actual = os.path.splitext(archivo)[1]
        if not extension_actual:
            # Preguntar qué extensión usar
            ext, ok = QInputDialog.getItem(
                self,
                "Seleccionar formato",
                "Elige la extensión del archivo:",
                ext_list,
                0,
                False
            )
            if not ok:
                return
            archivo += f".{ext}"
        else:
            # Verificar que la extensión sea válida
            extension_actual = extension_actual[1:].lower()
            if extension_actual not in ext_list:
                respuesta = QMessageBox.question(
                    self,
                    "Extensión no válida",
                    f"La extensión '.{extension_actual}' no está en la lista de formatos permitidos.\n"
                    f"Formatos permitidos: {', '.join(ext_list)}\n\n"
                    "¿Deseas continuar con la extensión actual?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if respuesta == QMessageBox.No:
                    return
        
        self.archivo_actual = archivo
        self.contrasena_archivo = None  # Resetear contraseña para nuevo archivo
        self.guardar_archivo()
    
    def cerrar_archivo(self):
        if self.historial.hay_cambios_pendientes():
            respuesta = QMessageBox.question(
                self, "Cambios sin guardar",
                "¿Deseas guardar los cambios antes de cerrar?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if respuesta == QMessageBox.Cancel:
                return
            elif respuesta == QMessageBox.Yes:
                self.guardar_archivo()
        
        self.archivo_actual = None
        self.archivo_cifrado = False
        self.contrasena_archivo = None
        self.text_edit.clear()
        self.mostrar_bienvenida()
        self.actualizar_barra_estado()
    
    def aumentar_tamano(self):
        """Aumenta el tamaño del texto (seleccionado o todo el documento)"""
        cursor = self.text_edit.textCursor()
        
        if cursor.hasSelection():
            # Cambiar solo el texto seleccionado
            formato = cursor.charFormat()
            tamano = formato.fontPointSize()
            if tamano <= 0:
                tamano = self.tamano_fuente_base
            nuevo_tamano = min(tamano + 2, 72)
            formato.setFontPointSize(nuevo_tamano)
            cursor.mergeCharFormat(formato)
        else:
            # Cambiar TODO el documento
            self.tamano_fuente_base = min(self.tamano_fuente_base + 2, 72)
            
            # Seleccionar todo el documento para aplicar el cambio
            cursor.select(QTextCursor.Document)
            formato = cursor.charFormat()
            formato.setFontPointSize(self.tamano_fuente_base)
            cursor.mergeCharFormat(formato)
            
            # Guardar configuración
            self.config.establecer('Editor', 'tamano_fuente', str(self.tamano_fuente_base))
            
            # Actualizar la fuente base
            fuente = self.text_edit.currentFont()
            fuente.setPointSize(self.tamano_fuente_base)
            self.text_edit.setFont(fuente)
            
            # Deseleccionar
            cursor.clearSelection()
            self.text_edit.setTextCursor(cursor)

    def disminuir_tamano(self):
        """Disminuye el tamaño del texto (seleccionado o todo el documento)"""
        cursor = self.text_edit.textCursor()
        
        if cursor.hasSelection():
            # Cambiar solo el texto seleccionado
            formato = cursor.charFormat()
            tamano = formato.fontPointSize()
            if tamano <= 0:
                tamano = self.tamano_fuente_base
            nuevo_tamano = max(tamano - 2, 6)
            formato.setFontPointSize(nuevo_tamano)
            cursor.mergeCharFormat(formato)
        else:
            # Cambiar TODO el documento
            self.tamano_fuente_base = max(self.tamano_fuente_base - 2, 6)
            
            # Seleccionar todo el documento para aplicar el cambio
            cursor.select(QTextCursor.Document)
            formato = cursor.charFormat()
            formato.setFontPointSize(self.tamano_fuente_base)
            cursor.mergeCharFormat(formato)
            
            # Guardar configuración
            self.config.establecer('Editor', 'tamano_fuente', str(self.tamano_fuente_base))
            
            # Actualizar la fuente base
            fuente = self.text_edit.currentFont()
            fuente.setPointSize(self.tamano_fuente_base)
            self.text_edit.setFont(fuente)
            
            # Deseleccionar
            cursor.clearSelection()
            self.text_edit.setTextCursor(cursor)
    
    # ==================== FIN FUNCIONES CORREGIDAS ====================
    
    def cambiar_fuente(self):
        fuente, ok = QFontDialog.getFont(self.text_edit.currentFont(), self)
        if ok:
            self.text_edit.setCurrentFont(fuente)
            self.config.establecer('Editor', 'fuente', fuente.family())
            self.config.establecer('Editor', 'tamano_fuente', str(fuente.pointSize()))
            self.tamano_fuente_base = fuente.pointSize()
    
    def insertar_imagen(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Insertar Imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if archivo:
            ancho, ok = QInputDialog.getInt(
                self, "Tamaño de Imagen",
                "¿Ancho en píxeles?", 200, 50, 1000
            )
            if ok:
                cursor = self.text_edit.textCursor()
                cursor.insertHtml(f'<img src="{archivo}" width="{ancho}">')
    
    def resaltar_texto(self):
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection():
                formato = cursor.charFormat()
                formato.setBackground(color)
                cursor.mergeCharFormat(formato)
    
    def buscar_texto(self):
        texto, ok = QInputDialog.getText(self, "Buscar", "Buscar texto:")
        if ok and texto:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(cursor.Start)
            self.text_edit.setTextCursor(cursor)
            if not self.text_edit.find(texto):
                QMessageBox.information(self, "Buscar", "Texto no encontrado")
    
    def mostrar_bienvenida(self):
        bienvenida = """
        <h1 style='color: #4CAF50; text-align: center;'>¡Bienvenido a CDV!</h1>
        <p style='color: #cccccc; text-align: center;'>Confidential Document Viewer</p>
        <p style='color: #888888; text-align: center;'>Editor de Texto Seguro - Modo Oscuro</p>
        <p style='color: #666666; text-align: center;'>Carga un archivo o comienza a escribir</p>
        <hr style='border-color: #4CAF50;'>
        <p style='color: #666666; text-align: center;'>
            <small>Ctrl+O: Abrir | Ctrl+S: Guardar | Ctrl+Z: Deshacer | Ctrl+Y: Rehacer</small>
        </p>
        """
        self.text_edit.setHtml(bienvenida)
        self.historial.limpiar()
        self.historial.guardar_estado(bienvenida)
        self.actualizar_acciones_edicion()
    
    def cambiar_clave(self):
        if not self.archivo_cifrado:
            QMessageBox.information(self, "Sin cifrar", 
                "El archivo actual no está cifrado. Guarda con contraseña para cifrarlo.")
            return
        
        dialog = PasswordDialog(
            "Cambiar contraseña",
            "Ingresa la nueva contraseña (mínimo 4 caracteres):",
            modo_guardar=True,
            parent=self
        )
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        nueva_contrasena = dialog.get_contrasena()
        
        contrasena_actual, ok = QInputDialog.getText(
            self, "Verificar contraseña actual",
            "Ingresa la contraseña actual para confirmar:",
            QLineEdit.Password
        )
        
        if not ok or contrasena_actual != self.contrasena_archivo:
            QMessageBox.critical(self, "Error", "Contraseña actual incorrecta.")
            return
        
        self.contrasena_archivo = nueva_contrasena
        self.guardar_archivo()
    
    def mostrar_acerca_de(self):
        version = "0.0.2P"
        algoritmo = self.config.obtener('Seguridad', 'algoritmo', 'aes').upper()
        crypto_status = "✓" if CRYPTOGRAPHY_AVAILABLE else "✗ (usando XOR)"
        
        QMessageBox.about(
            self, "Acerca de CDV",
            f"""
            <h2 style='color: #4CAF50;'>CDV - Confidential Document Viewer</h2>
            <p><b>Versión:</b> {version}</p>
            <p><b>Algoritmo de cifrado:</b> {algoritmo}</p>
            <p><b>Cryptography disponible:</b> {crypto_status}</p>
            <hr>
            <p>Características:</p>
            <ul>
                <li>Cifrado con contraseña (mínimo 4 caracteres)</li>
                <li>Formatos propios: .cdv, .sec, .enc</li>
                <li>Verificación de integridad</li>
                <li>Deshacer/Rehacer (Ctrl+Z/Y)</li>
                <li>Editor de texto enriquecido</li>
                <li>Configuración personalizable</li>
                <li>Modo Oscuro Completo</li>
            </ul>
            <p style='color: #666666;'><small>© 2026 Endry Cumare - Todos los derechos reservados</small></p>
            """
        )
    
    def closeEvent(self, event):
        if self.historial.hay_cambios_pendientes():
            respuesta = QMessageBox.question(
                self, "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Deseas guardarlos antes de salir?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if respuesta == QMessageBox.Yes:
                self.guardar_archivo()
                event.accept()
            elif respuesta == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        
        self.config.establecer('Ventana', 'ancho', str(self.width()))
        self.config.establecer('Ventana', 'alto', str(self.height()))
        self.config.establecer('Ventana', 'maximizada', str(self.isMaximized()))


# ==================== PUNTO DE ENTRADA ====================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CDV")
    app.setOrganizationName("CDV")
    
    os.makedirs("config", exist_ok=True)
    
    ventana = CDVEditor()
    ventana.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()