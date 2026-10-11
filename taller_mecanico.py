import tkinter as tk
import unicodedata
from tkinter import ttk, messagebox
import mysql.connector

from clientes import (
    actualizar_cliente,
    cargar_clientes,
    cargar_datos_clientes,
    eliminar_cliente,
    registrar_cliente,
)
from database import MYSQL_DATABASE, conectar_mysql
from usuarios import (
    actualizar_usuario,
    autenticar_usuario,
    cargar_usuarios,
    eliminar_usuario,
    registrar_usuario,
)
from vehiculos import (
    actualizar_vehiculo,
    cargar_vehiculos,
    eliminar_vehiculo,
    registrar_vehiculo,
)

def normalizar_busqueda(texto):
    texto = unicodedata.normalize("NFKD", str(texto).casefold())
    sin_acentos = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )
    return " ".join(
        "".join(caracter if caracter.isalnum() else " " for caracter in sin_acentos).split()
    )

def coincide_busqueda(consulta, campos):
    terminos = normalizar_busqueda(consulta).split()
    texto = normalizar_busqueda(" ".join(str(campo) for campo in campos))
    return bool(terminos) and all(termino in texto for termino in terminos)

def inicializar_base_datos():
    """Crea la base de datos y las tablas necesarias."""
    conexion = conectar_mysql(incluir_base=False)
    cursor = conexion.cursor()
    nombre_base = MYSQL_DATABASE.replace("`", "``")
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{nombre_base}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.close()
    conexion.close()

    conexion = conectar_mysql()
    cursor = conexion.cursor()
    sentencias = (
        """CREATE TABLE IF NOT EXISTS usuarios (
            id INT NOT NULL PRIMARY KEY,
            nombre VARCHAR(150) NOT NULL,
            telefono VARCHAR(40) NOT NULL,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            perfil VARCHAR(20) NOT NULL
        ) ENGINE=InnoDB""",
        """CREATE TABLE IF NOT EXISTS clientes (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            telefono VARCHAR(40) NOT NULL,
            direccion VARCHAR(255) NOT NULL,
            rfc VARCHAR(20) NOT NULL,
            UNIQUE KEY uq_cliente_datos (nombre, telefono, direccion, rfc)
        ) ENGINE=InnoDB""",
        """CREATE TABLE IF NOT EXISTS vehiculos (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            cliente_id INT NOT NULL,
            matricula VARCHAR(30) NOT NULL UNIQUE,
            marca VARCHAR(80) NOT NULL,
            modelo VARCHAR(80) NOT NULL,
            anio SMALLINT NOT NULL,
            color VARCHAR(60) NOT NULL,
            CONSTRAINT fk_vehiculo_cliente FOREIGN KEY (cliente_id)
                REFERENCES clientes(id)
        ) ENGINE=InnoDB""",
    )
    for sentencia in sentencias:
        cursor.execute(sentencia)

    cursor.execute("SHOW COLUMNS FROM clientes")
    columnas = {fila[0].lower() for fila in cursor.fetchall()}
    for nombre_columna, tipo, longitud in (
        ("telefono", "VARCHAR(40)", 40),
        ("direccion", "VARCHAR(255)", 255),
        ("rfc", "VARCHAR(20)", 20),
    ):
        if nombre_columna not in columnas:
            cursor.execute(
                f"ALTER TABLE clientes ADD COLUMN {nombre_columna} {tipo} NOT NULL DEFAULT ''"
            )

    cursor.execute("ALTER TABLE usuarios MODIFY id INT NOT NULL AUTO_INCREMENT")
    conexion.commit()
    cursor.close()
    conexion.close()

# ------------------ Interfaz Gráfica ------------------
class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Iniciar sesión")
        self.root.geometry("360x220")
        self.root.resizable(False, False)

        frame_login = ttk.LabelFrame(root, text="Acceso al Taller")
        frame_login.pack(fill="both", expand=True, padx=20, pady=20)

        ttk.Label(frame_login, text="Username:").grid(row=0, column=0, sticky="e", padx=8, pady=(16, 8))
        self.txt_username = ttk.Entry(frame_login)
        self.txt_username.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(16, 8))

        ttk.Label(frame_login, text="Password:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        self.txt_password = ttk.Entry(frame_login, show="*")
        self.txt_password.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=8)
        self.txt_password.bind("<Return>", self.iniciar_sesion)

        ttk.Button(
            frame_login,
            text="Iniciar sesión",
            command=self.iniciar_sesion,
        ).grid(row=2, column=0, columnspan=2, pady=(8, 14))
        frame_login.columnconfigure(1, weight=1)
        self.txt_username.focus_set()

    def iniciar_sesion(self, event=None):
        username = self.txt_username.get().strip()
        password = self.txt_password.get()
        if not username or not password:
            messagebox.showerror("Error", "Ingrese username y password")
            return

        usuario = autenticar_usuario(username, password)
        if usuario is None:
            self.txt_password.delete(0, tk.END)
            messagebox.showerror("Acceso denegado", "Username o password incorrectos")
            return

        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.resizable(True, True)
        TallerApp(self.root)

class TallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Taller Automotriz")
        self.root.geometry("700x550")

        menu_bar = tk.Menu(root)
        menu_modulos = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="file", menu=menu_modulos)
        root.config(menu=menu_bar)

        self.contenido = tk.Frame(root)
        self.contenido.pack(fill="both", expand=True, padx=10, pady=10)
        self.modulos = {}

        for nombre in ("Usuarios", "Clientes", "Vehículos", "Reparaciones", "Piezas"):
            frame = tk.Frame(self.contenido)
            self.modulos[nombre] = frame
            menu_modulos.add_command(
                label=nombre,
                command=lambda modulo=nombre: self.mostrar_modulo(modulo),
            )

        frame_busqueda_usuarios = tk.LabelFrame(self.modulos["Usuarios"], text="Buscar usuarios")
        frame_busqueda_usuarios.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_busqueda_usuarios, text="Datos:").pack(side="left", padx=(8, 4), pady=6)
        self.txt_buscar_usuario = tk.Entry(frame_busqueda_usuarios)
        self.txt_buscar_usuario.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=6)
        self.txt_buscar_usuario.bind("<Return>", self.buscar_usuarios)
        tk.Button(
            frame_busqueda_usuarios,
            text="Buscar",
            command=self.buscar_usuarios,
        ).pack(side="left", padx=(0, 8), pady=6)

        frame_usuarios = tk.LabelFrame(self.modulos["Usuarios"], text="Registro de Usuarios")
        frame_usuarios.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(frame_usuarios, text="Usuario ID:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.txt_usuario_id = ttk.Entry(frame_usuarios, state="readonly")
        self.txt_usuario_id.grid(row=0, column=1, sticky="ew", padx=5, pady=4)

        tk.Label(frame_usuarios, text="Nombre:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.txt_usuario_nombre = ttk.Entry(frame_usuarios)
        self.txt_usuario_nombre.grid(row=1, column=1, sticky="ew", padx=5, pady=4)

        tk.Label(frame_usuarios, text="Teléfono:").grid(row=2, column=0, sticky="e", padx=5, pady=4)
        self.txt_usuario_telefono = ttk.Entry(frame_usuarios)
        self.txt_usuario_telefono.grid(row=2, column=1, sticky="ew", padx=5, pady=4)

        tk.Label(frame_usuarios, text="Username:").grid(row=3, column=0, sticky="e", padx=5, pady=4)
        self.txt_usuario_username = ttk.Entry(frame_usuarios)
        self.txt_usuario_username.grid(row=3, column=1, sticky="ew", padx=5, pady=4)

        tk.Label(frame_usuarios, text="Password:").grid(row=4, column=0, sticky="e", padx=5, pady=4)
        self.txt_usuario_password = ttk.Entry(frame_usuarios, show="*")
        self.txt_usuario_password.grid(row=4, column=1, sticky="ew", padx=5, pady=4)

        tk.Label(frame_usuarios, text="Perfil:").grid(row=5, column=0, sticky="e", padx=5, pady=4)
        self.combo_usuario_perfil = ttk.Combobox(
            frame_usuarios,
            state="readonly",
            values=("admin", "mecanico", "encargado"),
        )
        self.combo_usuario_perfil.grid(row=5, column=1, sticky="ew", padx=5, pady=4)

        acciones_usuario = ttk.Frame(frame_usuarios)
        acciones_usuario.grid(row=6, column=0, columnspan=2, pady=8)
        ttk.Button(
            acciones_usuario,
            text="Registrar",
            command=self.registrar_usuario,
        ).pack(side="left", padx=3)
        ttk.Button(
            acciones_usuario,
            text="Actualizar",
            command=self.actualizar_usuario_form,
        ).pack(side="left", padx=3)
        ttk.Button(
            acciones_usuario,
            text="Borrar",
            command=self.borrar_usuario_form,
        ).pack(side="left", padx=3)
        ttk.Button(
            acciones_usuario,
            text="Cancelar",
            command=self.cancelar_usuario,
        ).pack(side="left", padx=3)
        frame_usuarios.columnconfigure(1, weight=1)

        frame_busqueda_clientes = tk.LabelFrame(self.modulos["Clientes"], text="Buscar clientes")
        frame_busqueda_clientes.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_busqueda_clientes, text="Datos:").pack(side="left", padx=(8, 4), pady=6)
        self.txt_buscar_cliente = tk.Entry(frame_busqueda_clientes)
        self.txt_buscar_cliente.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=6)
        self.txt_buscar_cliente.bind("<Return>", self.buscar_clientes)
        tk.Button(
            frame_busqueda_clientes,
            text="Buscar",
            command=self.buscar_clientes,
        ).pack(side="left", padx=(0, 8), pady=6)

        frame_clientes = tk.LabelFrame(self.modulos["Clientes"], text="Registro de Clientes")
        frame_clientes.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(frame_clientes, text="Cliente ID:").grid(row=0, column=0)
        self.txt_cliente_registro_id = ttk.Entry(frame_clientes, state="readonly")
        self.txt_cliente_registro_id.grid(row=0, column=1)

        tk.Label(frame_clientes, text="Nombre:").grid(row=1, column=0)
        self.txt_nombre = tk.Entry(frame_clientes)
        self.txt_nombre.grid(row=1, column=1)

        tk.Label(frame_clientes, text="Teléfono:").grid(row=2, column=0)
        self.txt_telefono = tk.Entry(frame_clientes)
        self.txt_telefono.grid(row=2, column=1)

        tk.Label(frame_clientes, text="Dirección:").grid(row=3, column=0)
        self.txt_direccion = tk.Entry(frame_clientes)
        self.txt_direccion.grid(row=3, column=1)

        tk.Label(frame_clientes, text="RFC:").grid(row=4, column=0)
        self.txt_rfc = tk.Entry(frame_clientes)
        self.txt_rfc.grid(row=4, column=1)

        acciones_clientes = ttk.Frame(frame_clientes)
        acciones_clientes.grid(row=5, column=0, columnspan=2, pady=8)
        ttk.Button(acciones_clientes, text="Registrar", command=self.registrar_cliente).pack(side="left", padx=3)
        ttk.Button(acciones_clientes, text="Actualizar", command=self.actualizar_cliente_form).pack(side="left", padx=3)
        ttk.Button(acciones_clientes, text="Borrar", command=self.borrar_cliente_form).pack(side="left", padx=3)
        ttk.Button(acciones_clientes, text="Cancelar", command=self.cancelar_cliente).pack(side="left", padx=3)

        # -------Frame Vehículos------- #
        frame_busqueda_vehiculos = tk.LabelFrame(self.modulos["Vehículos"], text="Buscar vehículos")
        frame_busqueda_vehiculos.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_busqueda_vehiculos, text="Datos:").pack(side="left", padx=(8, 4), pady=6)
        self.txt_buscar_vehiculo = tk.Entry(frame_busqueda_vehiculos)
        self.txt_buscar_vehiculo.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=6)
        self.txt_buscar_vehiculo.bind("<Return>", self.buscar_vehiculos)
        tk.Button(
            frame_busqueda_vehiculos,
            text="Buscar",
            command=self.buscar_vehiculos,
        ).pack(side="left", padx=(0, 8), pady=6)

        frame_vehiculos = tk.LabelFrame(self.modulos["Vehículos"], text="Registro de Vehículos")
        frame_vehiculos.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(frame_vehiculos, text="Matrícula:").grid(row=0, column=0)
        self.txt_matricula = tk.Entry(frame_vehiculos)
        self.txt_matricula.grid(row=0, column=1)

        tk.Label(frame_vehiculos, text="Vehículo ID:").grid(row=0, column=2)
        self.txt_vehiculo_id = ttk.Entry(frame_vehiculos, state="readonly", width=8)
        self.txt_vehiculo_id.grid(row=0, column=3)

        tk.Label(frame_vehiculos, text="Cliente:").grid(row=1, column=0)
        self.combo_clientes = ttk.Combobox(frame_vehiculos, state="readonly", width=32)
        self.combo_clientes.grid(row=1, column=1)
        self.combo_clientes.bind("<<ComboboxSelected>>", self.mostrar_id_cliente)

        tk.Label(frame_vehiculos, text="ID:").grid(row=1, column=2)
        self.txt_cliente_id = ttk.Entry(frame_vehiculos, state="readonly", width=8)
        self.txt_cliente_id.grid(row=1, column=3)

        tk.Label(frame_vehiculos, text="Marca:").grid(row=2, column=0)
        self.txt_marca = tk.Entry(frame_vehiculos)
        self.txt_marca.grid(row=2, column=1)

        tk.Label(frame_vehiculos, text="Modelo:").grid(row=3, column=0)
        self.txt_modelo = tk.Entry(frame_vehiculos)
        self.txt_modelo.grid(row=3, column=1)

        tk.Label(frame_vehiculos, text="Año:").grid(row=4, column=0)
        self.txt_año = tk.Entry(frame_vehiculos)
        self.txt_año.grid(row=4, column=1)

        tk.Label(frame_vehiculos, text="Color:").grid(row=5, column=0)
        self.txt_color = tk.Entry(frame_vehiculos)
        self.txt_color.grid(row=5, column=1)

        acciones_vehiculos = ttk.Frame(frame_vehiculos)
        acciones_vehiculos.grid(row=6, column=0, columnspan=4, pady=8)
        ttk.Button(acciones_vehiculos, text="Registrar", command=self.registrar_vehiculo).pack(side="left", padx=3)
        ttk.Button(acciones_vehiculos, text="Actualizar", command=self.actualizar_vehiculo_form).pack(side="left", padx=3)
        ttk.Button(acciones_vehiculos, text="Borrar", command=self.borrar_vehiculo_form).pack(side="left", padx=3)
        ttk.Button(acciones_vehiculos, text="Cancelar", command=self.cancelar_vehiculo).pack(side="left", padx=3)

        self.actualizar_usuarios()
        self.actualizar_clientes()

    def mostrar_modulo(self, nombre):
        for frame in self.modulos.values():
            frame.pack_forget()
        self.modulos[nombre].pack(fill="both", expand=True)

    def actualizar_usuarios(self):
        self.usuarios = cargar_usuarios()

    def registrar_usuario(self):
        nombre = self.txt_usuario_nombre.get().strip()
        telefono = self.txt_usuario_telefono.get().strip()
        username = self.txt_usuario_username.get().strip()
        password = self.txt_usuario_password.get()
        perfil = self.combo_usuario_perfil.get()

        if not nombre or not telefono or not username or not password or not perfil:
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return

        usuario_id = registrar_usuario(nombre, telefono, username, password, perfil)
        if usuario_id is None:
            messagebox.showwarning("Usuario duplicado", "Ese username ya está registrado")
            return

        self.actualizar_usuarios()
        self.mostrar_datos_usuario(self.usuarios[-1])
        messagebox.showinfo("Éxito", f"Usuario registrado con ID {usuario_id}")

    def actualizar_usuario_form(self):
        usuario_id = self.txt_usuario_id.get().strip()
        nombre = self.txt_usuario_nombre.get().strip()
        telefono = self.txt_usuario_telefono.get().strip()
        username = self.txt_usuario_username.get().strip()
        password = self.txt_usuario_password.get()
        perfil = self.combo_usuario_perfil.get()

        if not usuario_id:
            messagebox.showwarning("Selecciona un usuario", "Busca primero el usuario que deseas actualizar")
            return
        if not nombre or not telefono or not username or perfil not in ("admin", "mecanico", "encargado"):
            messagebox.showerror("Error", "Nombre, teléfono, username y perfil son obligatorios")
            return

        resultado = actualizar_usuario(
            int(usuario_id), nombre, telefono, username, perfil, password
        )
        if resultado is None:
            messagebox.showwarning("Username duplicado", "Ese username ya está asignado a otro usuario")
            return
        if not resultado:
            messagebox.showerror("Error", "El usuario ya no existe en la base de datos")
            self.cancelar_usuario()
            return

        self.actualizar_usuarios()
        usuario_actualizado = next(
            usuario for usuario in self.usuarios if int(usuario["id"]) == int(usuario_id)
        )
        self.mostrar_datos_usuario(usuario_actualizado)
        messagebox.showinfo("Éxito", "Usuario actualizado correctamente")

    def borrar_usuario_form(self):
        usuario_id = self.txt_usuario_id.get().strip()
        if not usuario_id:
            messagebox.showwarning("Selecciona un usuario", "Busca primero el usuario que deseas borrar")
            return

        username = self.txt_usuario_username.get().strip()
        if not messagebox.askyesno(
            "Confirmar borrado",
            f"¿Deseas borrar al usuario {username}? Esta acción no se puede deshacer.",
        ):
            return

        resultado = eliminar_usuario(int(usuario_id))
        if resultado == "ultimo_admin":
            messagebox.showwarning(
                "Operación no permitida",
                "No se puede borrar el último usuario con perfil admin.",
            )
            return
        if not resultado:
            messagebox.showerror("Error", "El usuario ya no existe en la base de datos")
            self.cancelar_usuario()
            return

        self.actualizar_usuarios()
        self.cancelar_usuario()
        messagebox.showinfo("Éxito", "Usuario borrado correctamente")

    def buscar_usuarios(self, event=None):
        consulta = self.txt_buscar_usuario.get().strip().casefold()
        if not consulta:
            return

        encontrados = [
            usuario for usuario in self.usuarios
            if coincide_busqueda(
                consulta,
                (
                    usuario.get("id", ""),
                    usuario.get("nombre", ""),
                    usuario.get("telefono", ""),
                    usuario.get("username", ""),
                    usuario.get("perfil", ""),
                ),
            )
        ]
        if not encontrados:
            self.limpiar_campos_usuario()
            messagebox.showinfo("Sin coincidencias", "No se encontró ningún usuario con esos datos.")
        elif len(encontrados) == 1:
            self.mostrar_datos_usuario(encontrados[0])
        else:
            self.limpiar_campos_usuario()
            messagebox.showinfo(
                "Búsqueda",
                f"Hay {len(encontrados)} usuarios coincidentes. Escribe más datos para precisar la búsqueda.",
            )

    def mostrar_datos_usuario(self, usuario):
        self.txt_usuario_id.configure(state="normal")
        self.txt_usuario_id.delete(0, tk.END)
        self.txt_usuario_id.insert(0, usuario["id"])
        self.txt_usuario_id.configure(state="readonly")

        for campo, valor in (
            (self.txt_usuario_nombre, usuario["nombre"]),
            (self.txt_usuario_telefono, usuario["telefono"]),
            (self.txt_usuario_username, usuario["username"]),
        ):
            campo.delete(0, tk.END)
            campo.insert(0, valor)
        self.txt_usuario_password.delete(0, tk.END)
        self.combo_usuario_perfil.set(usuario["perfil"])

    def limpiar_campos_usuario(self):
        self.txt_usuario_id.configure(state="normal")
        self.txt_usuario_id.delete(0, tk.END)
        self.txt_usuario_id.configure(state="readonly")
        for campo in (
            self.txt_usuario_nombre,
            self.txt_usuario_telefono,
            self.txt_usuario_username,
            self.txt_usuario_password,
        ):
            campo.delete(0, tk.END)
        self.combo_usuario_perfil.set("")

    def cancelar_usuario(self):
        self.txt_buscar_usuario.delete(0, tk.END)
        self.limpiar_campos_usuario()

    def cancelar_cliente(self):
        self.txt_buscar_cliente.delete(0, tk.END)
        self.txt_cliente_registro_id.configure(state="normal")
        self.txt_cliente_registro_id.delete(0, tk.END)
        self.txt_cliente_registro_id.configure(state="readonly")
        for campo in (self.txt_nombre, self.txt_telefono, self.txt_direccion, self.txt_rfc):
            campo.delete(0, tk.END)

    def cancelar_vehiculo(self):
        self.txt_buscar_vehiculo.delete(0, tk.END)
        self.txt_vehiculo_id.configure(state="normal")
        self.txt_vehiculo_id.delete(0, tk.END)
        self.txt_vehiculo_id.configure(state="readonly")
        for campo in (self.txt_matricula, self.txt_marca, self.txt_modelo, self.txt_año, self.txt_color):
            campo.delete(0, tk.END)
        self.combo_clientes.set("")
        self.mostrar_id_cliente()

    def registrar_cliente(self):
        nombre = self.txt_nombre.get().strip()
        telefono = self.txt_telefono.get().strip()
        direccion = self.txt_direccion.get().strip()
        rfc = self.txt_rfc.get().strip()

        if not nombre or not telefono or not direccion or not rfc:
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return

        cliente_id = registrar_cliente(nombre, telefono, direccion, rfc)
        if cliente_id is None:
            messagebox.showwarning("Cliente duplicado", "Ya existe un cliente con esos datos")
            return
        messagebox.showinfo("Éxito", f"Cliente registrado con ID {cliente_id}")
        self.actualizar_clientes()

    def actualizar_cliente_form(self):
        cliente_id = self.txt_cliente_registro_id.get().strip()
        datos = (
            self.txt_nombre.get().strip(),
            self.txt_telefono.get().strip(),
            self.txt_direccion.get().strip(),
            self.txt_rfc.get().strip(),
        )
        if not cliente_id:
            messagebox.showwarning("Selecciona un cliente", "Busca primero el cliente que deseas actualizar")
            return
        if not all(datos):
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return

        resultado = actualizar_cliente(int(cliente_id), *datos)
        if resultado is None:
            messagebox.showwarning("Cliente duplicado", "Ya existe otro cliente con esos datos")
        elif not resultado:
            messagebox.showerror("Error", "El cliente ya no existe en la base de datos")
            self.cancelar_cliente()
        else:
            self.actualizar_clientes()
            self.mostrar_datos_cliente(int(cliente_id))
            messagebox.showinfo("Éxito", "Cliente actualizado correctamente")

    def borrar_cliente_form(self):
        cliente_id = self.txt_cliente_registro_id.get().strip()
        if not cliente_id:
            messagebox.showwarning("Selecciona un cliente", "Busca primero el cliente que deseas borrar")
            return
        nombre = self.txt_nombre.get().strip()
        if not messagebox.askyesno(
            "Confirmar borrado",
            f"¿Deseas borrar al cliente {nombre}? Esta acción no se puede deshacer.",
        ):
            return

        resultado = eliminar_cliente(int(cliente_id))
        if resultado == "con_vehiculos":
            messagebox.showwarning(
                "No se puede borrar",
                "Primero borra los vehículos asociados a este cliente.",
            )
        elif not resultado:
            messagebox.showerror("Error", "El cliente ya no existe en la base de datos")
            self.cancelar_cliente()
        else:
            self.cancelar_cliente()
            self.actualizar_clientes()
            messagebox.showinfo("Éxito", "Cliente borrado correctamente")

    def registrar_vehiculo(self):
        cliente = self.combo_clientes.get()
        if not cliente:
            messagebox.showerror("Error", "Seleccione un cliente")
            return

        cliente_id = self.txt_cliente_id.get()
        if not cliente_id:
            messagebox.showerror("Error", "Seleccione un cliente")
            return

        matricula = self.txt_matricula.get().strip()
        marca = self.txt_marca.get().strip()
        modelo = self.txt_modelo.get().strip()
        año = self.txt_año.get().strip()
        color = self.txt_color.get().strip()

        if not matricula or not marca or not modelo or not año.isdigit() or not color:
            messagebox.showerror("Error", "Datos de vehículo inválidos")
            return

        registrado = registrar_vehiculo(int(cliente_id), matricula, marca, modelo, año, color)
        if not registrado:
            messagebox.showwarning("Vehículo duplicado", "Ya existe un vehículo con esa matrícula")
            return
        messagebox.showinfo("Éxito", "Vehículo registrado correctamente")
        self.buscar_vehiculos()

    def actualizar_vehiculo_form(self):
        vehiculo_id = self.txt_vehiculo_id.get().strip()
        cliente_id = self.txt_cliente_id.get().strip()
        matricula = self.txt_matricula.get().strip()
        marca = self.txt_marca.get().strip()
        modelo = self.txt_modelo.get().strip()
        año = self.txt_año.get().strip()
        color = self.txt_color.get().strip()

        if not vehiculo_id:
            messagebox.showwarning("Selecciona un vehículo", "Busca primero el vehículo que deseas actualizar")
            return
        if not cliente_id or not matricula or not marca or not modelo or not año.isdigit() or not color:
            messagebox.showerror("Error", "Completa todos los campos del vehículo")
            return

        resultado = actualizar_vehiculo(
            int(vehiculo_id), int(cliente_id), matricula, marca, modelo, año, color
        )
        if resultado is None:
            messagebox.showwarning("Matrícula duplicada", "Ya existe otro vehículo con esa matrícula")
        elif not resultado:
            messagebox.showerror("Error", "El vehículo ya no existe o el cliente seleccionado no es válido")
            self.cancelar_vehiculo()
        else:
            self.buscar_vehiculos()
            messagebox.showinfo("Éxito", "Vehículo actualizado correctamente")

    def borrar_vehiculo_form(self):
        vehiculo_id = self.txt_vehiculo_id.get().strip()
        matricula = self.txt_matricula.get().strip()
        if not vehiculo_id:
            messagebox.showwarning("Selecciona un vehículo", "Busca primero el vehículo que deseas borrar")
            return
        if not messagebox.askyesno(
            "Confirmar borrado",
            f"¿Deseas borrar el vehículo con matrícula {matricula}? Esta acción no se puede deshacer.",
        ):
            return

        if not eliminar_vehiculo(int(vehiculo_id)):
            messagebox.showerror("Error", "El vehículo ya no existe en la base de datos")
            self.cancelar_vehiculo()
            return
        self.cancelar_vehiculo()
        messagebox.showinfo("Éxito", "Vehículo borrado correctamente")

    def mostrar_id_cliente(self, event=None):
        indice = self.combo_clientes.current()
        cliente_id = list(self.clientes.keys())[indice] if indice >= 0 else ""
        self.txt_cliente_id.configure(state="normal")
        self.txt_cliente_id.delete(0, tk.END)
        self.txt_cliente_id.insert(0, cliente_id)
        self.txt_cliente_id.configure(state="readonly")

    def actualizar_clientes(self):
        self.clientes = cargar_clientes()
        self.datos_clientes = cargar_datos_clientes()
        self.combo_clientes["values"] = list(self.clientes.values())
        self.combo_clientes.set("")
        self.mostrar_id_cliente()
        self.buscar_clientes()

    def buscar_clientes(self, event=None):
        consulta = self.txt_buscar_cliente.get().strip()
        if not consulta:
            return

        encontrados = [
            cliente_id
            for cliente_id, datos in self.datos_clientes.items()
            if coincide_busqueda(consulta, (cliente_id, *datos))
        ]
        if not encontrados:
            messagebox.showinfo("Sin coincidencias", "No se encontró ningún cliente con esos datos.")
            self.limpiar_campos_cliente()
        elif len(encontrados) == 1:
            self.mostrar_datos_cliente(encontrados[0])
        else:
            self.limpiar_campos_cliente()
            messagebox.showinfo(
                "Búsqueda",
                f"Hay {len(encontrados)} clientes coincidentes. Escribe más datos para precisar la búsqueda.",
            )

    def mostrar_datos_cliente(self, cliente_id):
        datos = self.datos_clientes.get(int(cliente_id))
        if datos:
            self.txt_cliente_registro_id.configure(state="normal")
            self.txt_cliente_registro_id.delete(0, tk.END)
            self.txt_cliente_registro_id.insert(0, str(cliente_id))
            self.txt_cliente_registro_id.configure(state="readonly")
            for campo, valor in zip(
                (self.txt_nombre, self.txt_telefono, self.txt_direccion, self.txt_rfc), datos
            ):
                campo.delete(0, tk.END)
                campo.insert(0, valor)

    def limpiar_campos_cliente(self):
        self.txt_cliente_registro_id.configure(state="normal")
        self.txt_cliente_registro_id.delete(0, tk.END)
        self.txt_cliente_registro_id.configure(state="readonly")
        for campo in (self.txt_nombre, self.txt_telefono, self.txt_direccion, self.txt_rfc):
            campo.delete(0, tk.END)

    def buscar_vehiculos(self, event=None):
        consulta = self.txt_buscar_vehiculo.get().strip()
        if not consulta:
            return

        encontrados = []
        for vehiculo_id, cliente_id, matricula, marca, modelo, año, color in cargar_vehiculos():
            campos = (
                vehiculo_id,
                cliente_id,
                matricula,
                marca,
                modelo,
                año,
                color,
                self.clientes.get(int(cliente_id), ""),
            )
            if coincide_busqueda(consulta, campos):
                encontrados.append((vehiculo_id, cliente_id, matricula, marca, modelo, año, color))
        if not encontrados:
            messagebox.showinfo("Sin coincidencias", "No se encontró ningún vehículo con esos datos.")
            self.limpiar_campos_vehiculo()
        elif len(encontrados) == 1:
            self.mostrar_datos_vehiculo(encontrados[0])
        else:
            self.limpiar_campos_vehiculo()
            messagebox.showinfo(
                "Búsqueda",
                f"Hay {len(encontrados)} vehículos coincidentes. Escribe más datos para precisar la búsqueda.",
            )

    def limpiar_campos_vehiculo(self):
        self.txt_vehiculo_id.configure(state="normal")
        self.txt_vehiculo_id.delete(0, tk.END)
        self.txt_vehiculo_id.configure(state="readonly")
        for campo in (
            self.txt_matricula,
            self.txt_marca,
            self.txt_modelo,
            self.txt_año,
            self.txt_color,
        ):
            campo.delete(0, tk.END)
        self.combo_clientes.set("")
        self.mostrar_id_cliente()

    def mostrar_datos_vehiculo(self, datos):
        vehiculo_id, cliente_id, matricula, marca, modelo, año, color = datos
        self.txt_vehiculo_id.configure(state="normal")
        self.txt_vehiculo_id.delete(0, tk.END)
        self.txt_vehiculo_id.insert(0, str(vehiculo_id))
        self.txt_vehiculo_id.configure(state="readonly")
        for campo, valor in zip(
            (self.txt_matricula, self.txt_marca, self.txt_modelo, self.txt_año, self.txt_color),
            (matricula, marca, modelo, año, color),
        ):
            campo.delete(0, tk.END)
            campo.insert(0, valor)

        cliente_ids = list(self.clientes)
        if int(cliente_id) in self.clientes:
            self.combo_clientes.current(cliente_ids.index(int(cliente_id)))
        else:
            self.combo_clientes.set("")
        self.mostrar_id_cliente()

# ------------------ Main ------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    try:
        inicializar_base_datos()
    except mysql.connector.Error as error:
        messagebox.showerror(
            "Error de base de datos",
            "No se pudo conectar o inicializar la base de datos MySQL. "
            "Inicia MySQL desde XAMPP y verifica MYSQL_HOST, MYSQL_PORT, "
            "MYSQL_USER y MYSQL_PASSWORD.\n\n"
            f"Detalle: {error}",
        )
        root.destroy()
        raise SystemExit(1)
    root.deiconify()
    app = LoginApp(root)
    root.mainloop()
