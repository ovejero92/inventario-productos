# _IMPORTACION
import sqlite3
import os 
from colorama import Fore,init, Style 
from datetime import datetime
# from pathlib import Path

# _CONFIGURACION 
RUTA_DB = "inventario.db"
CARPETA_LOGS = "logs"
RUTA_LOG = f"{CARPETA_LOGS}/inventario.log"

os.makedirs(CARPETA_LOGS, exist_ok=True)

def registrar_log(nivel, mensaje):
    """ agrega uina linea al archivo .log """
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"{fecha_hora} | {nivel} | {mensaje}\n"
    with open(RUTA_LOG,"a",encoding="utf-8") as archivo:
        archivo.write(linea)

# LOS MENSAJES CON COLORAMA
def mostrar_exito(texto):
    print(Fore.GREEN + f"✔ {texto}")  # ✔ producto agregado correctamente

def mostrar_error(texto):
    print(Fore.RED + f"✘ {texto}")

def mostrar_aviso(texto):
    print(Fore.YELLOW + f"! {texto}")

def mostrar_titulo(texto):
    print()
    print(Fore.CYAN + Style.BRIGHT + f"=== {texto} ===")

# BASE DE DATOS 
def ejecutar_consulta(sql, parametros = (), traer_datos=False):
    conexion = sqlite3.connect(RUTA_DB)
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)

        if traer_datos:
            return cursor.fetchall()

        conexion.commit()
        return cursor.rowcount
    except sqlite3.Error as error:
        mostrar_error(f"Error en la base de datos: {error}")
        registrar_log("ERROR", f"Base de datos: {error}")
        return [] if traer_datos else 0
    finally:
        conexion.close()

def crear_tabla():
    sql = """
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            cantidad INTEGER NOT NULL,
            precio REAL NOT NULL,
            categoria TEXT
        )
    """
    ejecutar_consulta(sql)
    registrar_log("INFO","Programa inicado. Tabla 'productos' verificado.")

# _VALIDACIONES 
def pedir_texto(mensaje, obligatorio=True, actual=None):
    while True:
        if actual is not None:
            texto = input(f"{mensaje} [{actual}]: ").strip()
            if texto == "":
                return actual
            return texto

        texto = input(f"{mensaje}: ").strip()
        if texto == "" and obligatorio:
            mostrar_error("Este campo no puede estar vacío.")
            continue
        return texto

def pedir_entero(mensaje, actual=None):
    while True:
        if actual is not None:
            texto = input(f"{mensaje} [{actual}]: ").strip()
            if texto == "":
                return actual
        else:
            texto = input(f"{mensaje}: ").strip()

        try:
            numero = int(texto)
            if numero < 0:
                mostrar_error("El número no puede ser negativo.")
                continue
            return numero
        except ValueError:
            mostrar_error("Ingresá un número entero válido (ej: 10).")

def pedir_decimal(mensaje, actual=None):
    while True:
        if actual is not None:
            texto = input(f"{mensaje} [{actual}]: ").strip()
            if texto == "":
                return actual
        else:
            texto = input(f"{mensaje}: ").strip()

        try:
            numero = float(texto.replace(",", "."))
            if numero < 0:
                mostrar_error("El número no puede ser negativo.")
                continue
            return numero
        except ValueError:
            mostrar_error("Ingresá un número válido (ej: 1500.50).")

def confirmar(mensaje:str) -> bool:
    respuesta = input(f"{mensaje} (s/n): ").strip().lower()
    return respuesta == "s"

# LOGICA DE CRUD 
# MOSTRAR PRODUCTOS  ( READ )

def mostrar_tabla(productos):
    if not productos:
        mostrar_aviso("No hay productos para mostrar.")
        return

    encabezado = f"{'ID':<5}{'NOMBRE':<22}{'CANT.':<8}{'PRECIO':<12}{'CATEGORÍA':<16}DESCRIPCIÓN"
    print(Fore.CYAN + Style.BRIGHT + encabezado)
    print(Fore.CYAN + "-" * 85)

    for producto in productos:
        id_, nombre, descripcion, cantidad, precio, categoria = producto
        print(
            f"{id_:<5}{nombre[:20]:<22}{cantidad:<8}"
            f"${precio:<11.2f}{(categoria or '')[:14]:<16}{descripcion or ''}"
        )

    print(Fore.CYAN + "-" * 85)
    print(f"Total: {len(productos)} producto(s)")

def obtener_producto_por_id(id_producto):
    resultado = ejecutar_consulta(
        "SELECT * FROM productos WHERE id = ?", (id_producto,), traer_datos=True
    )
    return resultado[0] if resultado else None

# FUNCIONALIDADES 
# ( CREATE )

def registrar_producto():
    mostrar_titulo("REGISTRAR PRODUCTO")
    nombre = pedir_texto("Nombre")
    descripcion = pedir_texto("Descripción (opcional)", obligatorio=False)
    cantidad = pedir_entero("Cantidad")
    precio = pedir_decimal("Precio")
    categoria = pedir_texto("Categoría (opcional)", obligatorio=False)

    sql = """
        INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
        VALUES (?, ?, ?, ?, ?)
    """
    filas = ejecutar_consulta(sql, (nombre, descripcion, cantidad, precio, categoria))
    if filas > 0:
        mostrar_exito(f"Producto '{nombre}' registrado correctamente.")
        registrar_log("INFO", f"Producto registrado: {nombre} (cant: {cantidad}, precio: {precio})")

def ver_productos():
    mostrar_titulo("LISTADO DE PRODUCTOS")
    productos = ejecutar_consulta("SELECT * FROM productos ORDER BY id", traer_datos=True)
    mostrar_tabla(productos)
    registrar_log("INFO", "Se consultó el listado de productos.")

def actualizar_producto():
    mostrar_titulo("ACTUALIZAR PRODUCTO")
    id_producto = pedir_entero("ID del producto a actualizar")
    producto = obtener_producto_por_id(id_producto)

    if producto is None:
        mostrar_error(f"No existe un producto con ID {id_producto}.")
        return

    _, nombre, descripcion, cantidad, precio, categoria = producto

    mostrar_aviso("Presioná Enter para mantener el valor actual.")
    nuevo_nombre = pedir_texto("Nombre", actual=nombre)
    nueva_descripcion = pedir_texto("Descripción", actual=descripcion or "")
    nueva_cantidad = pedir_entero("Cantidad", actual=cantidad)
    nuevo_precio = pedir_decimal("Precio", actual=precio)
    nueva_categoria = pedir_texto("Categoría", actual=categoria or "")

    sql = """
        UPDATE productos
        SET nombre = ?, descripcion = ?, cantidad = ?, precio = ?, categoria = ?
        WHERE id = ?
    """
    filas = ejecutar_consulta(sql, (nuevo_nombre, nueva_descripcion, nueva_cantidad, nuevo_precio, nueva_categoria, id_producto))
    if filas > 0:
        mostrar_exito("Producto actualizado correctamente.")
        registrar_log("INFO", f"Producto actualizado: ID {id_producto} ({nuevo_nombre})")

def eliminar_producto():
    mostrar_titulo("ELIMINAR PRODUCTO")
    id_producto = pedir_entero("ID del producto a eliminar")
    producto = obtener_producto_por_id(id_producto)

    if producto is None:
        mostrar_error(f"No existe un producto con ID {id_producto}.")
        return

    mostrar_tabla([producto])
    if not confirmar("¿Seguro que querés eliminarlo?"):
        mostrar_aviso("Eliminación cancelada.")
        return

    filas = ejecutar_consulta("DELETE FROM productos WHERE id = ?", (id_producto,))
    if filas > 0:
        mostrar_exito("Producto eliminado correctamente.")
        registrar_log("WARNING", f"Producto eliminado: ID {id_producto} ({producto[1]})")



def mostrar_menu():
    print()
    print(Fore.MAGENTA + Style.BRIGHT + "╔══════════════════════════════════╗")
    print(Fore.MAGENTA + Style.BRIGHT + "║       SISTEMA DE INVENTARIO      ║")
    print(Fore.MAGENTA + Style.BRIGHT + "╚══════════════════════════════════╝")
    print("1. Registrar producto")
    print("2. Ver productos")
    print("3. Actualizar producto")
    print("4. Eliminar producto")
    print("0. Salir")

def main():
    crear_tabla()
    acciones = {
        "1": registrar_producto, "2": ver_productos, "3": actualizar_producto,
        "4": eliminar_producto,
    }

    while True:
        mostrar_menu()
        opcion = input("Elegí una opción: ").strip()
        if opcion == "0":
            registrar_log("INFO", "Programa finalizado.")
            print(Fore.CYAN + "¡Hasta luego!")
            break
        elif opcion in acciones:
            acciones[opcion]()
        else:
            mostrar_error("Opción inválida. Probá de nuevo.")

if __name__ == "__main__":
    main()
# condicion para ejecutar este modulo como modulo principal ( que no entre en loop)