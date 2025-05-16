#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Creator - Herramienta para combinar archivos HTML en un PDF

Este script toma múltiples archivos HTML de una carpeta, los ordena
y los combina en un único documento PDF, respetando el contenido y formato.
Funciona tanto de forma interactiva como con argumentos de línea de comandos.
"""

# Imports estándar
import os
import sys
import glob
import json
import re
import tempfile
import argparse
from pathlib import Path

# Verificar dependencias antes de continuar
try:
    # Imports de terceros
    from weasyprint import HTML, CSS
    from weasyprint.document import Document
except ImportError:
    print("\033[91mError: Dependencias faltantes.\033[0m")
    print("Este script requiere WeasyPrint para funcionar. Por favor, asegúrate de:")
    print("  1. Estar utilizando el entorno virtual correcto")
    print("  2. Haber instalado las dependencias con: pip install -r requirements.txt")
    print("\nSi estás fuera del entorno virtual, actívalo con:")
    print("  source venv/bin/activate  # En Linux/Mac")
    sys.exit(1)

# Constantes
CONFIG_DIR = os.path.expanduser("~/.config/pdf-creator")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")

# --- Estilos CSS ---
STYLES = {
    "landscape": CSS(string="@page { size: 29.7cm 21cm; margin: 1cm; }"),
    "portrait": CSS(string="@page { size: 21cm 29.7cm; margin: 1cm; }"),
    "measure": CSS(string="@page { size: auto; margin: 0; }"),
}


# --- Funciones de utilidad ---
def natural_sort_key(s):
    """
    Ordena cadenas que contienen números de forma natural.

    Args:
        s (str): Cadena a ordenar

    Returns:
        list: Lista de elementos para comparación de orden natural

    Ejemplo:
        ['sesion1.html', 'sesion2.html', 'sesion10.html'] en lugar de
        ['sesion1.html', 'sesion10.html', 'sesion2.html']
    """
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split("([0-9]+)", s)
    ]


# --- Funciones principales ---
def find_html_files(folder_path):
    """
    Encuentra y ordena archivos HTML en la carpeta especificada usando orden numérico natural.

    Esto asegura que los archivos se ordenen correctamente (ej: sesion1.html,
    sesion2.html, ..., sesion10.html) en lugar de usar orden alfabético estándar.

    Args:
        folder_path (str): Ruta a la carpeta con archivos HTML

    Returns:
        list: Lista ordenada de rutas a archivos HTML o lista vacía
    """
    search_path = os.path.join(folder_path, "*.html")
    html_files = sorted(glob.glob(search_path), key=natural_sort_key)

    if not html_files:
        print(f"Advertencia: No se encontraron archivos HTML en: {folder_path}")

    return html_files


# Esta función se ha incorporado directamente en create_pdf_from_html_folder para simplificar el código


def create_pdf_from_html_folder(
    input_folder, output_pdf_filename, orientation="landscape"
):
    """
    Crea un PDF a partir de todos los archivos HTML encontrados en una carpeta.

    Preserva el contenido completo de cada archivo HTML, permitiendo que fluya
    naturalmente a través de múltiples páginas si es necesario, mientras asegura
    que las tablas y otros elementos no se dividan entre páginas.

    Args:
        input_folder (str): Ruta a la carpeta con archivos HTML
        output_pdf_filename (str): Nombre del archivo PDF de salida
        orientation (str): "landscape" (apaisado) o "portrait" (vertical)

    Returns:
        bool: True si el proceso fue exitoso, False en caso contrario
    """
    # Validar el directorio de entrada
    if not os.path.isdir(input_folder):
        print(f"Error: La carpeta '{input_folder}' no existe o no es un directorio.")
        return False

    # Encontrar archivos HTML
    html_files = find_html_files(input_folder)
    if not html_files:
        print("No hay archivos HTML para procesar. Saliendo.")
        return False

    print(f"Archivos HTML encontrados (en orden): {len(html_files)}")

    # Crear directorio temporal para los archivos intermedios
    temp_dir = tempfile.mkdtemp(prefix="pdf_creator_")
    temp_pdf_files = []
    all_html_docs = []

    try:
        # Definir estilos CSS para preservar el contenido
        preserve_content_style = get_content_preservation_css(orientation)

        # Procesar cada archivo HTML
        for i, html_file in enumerate(html_files):
            print(f"Procesando archivo: {html_file}...")

            # Crear y guardar PDF temporal
            temp_pdf = os.path.join(temp_dir, f"doc_{i}.pdf")
            temp_pdf_files.append(temp_pdf)

            # Convertir HTML a PDF preservando el contenido
            html_doc = HTML(filename=html_file, base_url=input_folder)
            html_doc.write_pdf(temp_pdf, stylesheets=[preserve_content_style])

            print(f"  ✓ Procesado como '{os.path.basename(temp_pdf)}'")
            all_html_docs.append(html_doc)

        # Renderizar documentos y combinar páginas
        return combine_documents_to_pdf(all_html_docs, output_pdf_filename, orientation)
    except Exception as e:
        print(f"Error al crear el PDF: {e}")
        return False
    finally:
        # Limpiar archivos temporales
        cleanup_temp_files(temp_pdf_files, temp_dir)


def get_content_preservation_css(orientation):
    """
    Crea un estilo CSS que preserva el contenido y evita que las tablas
    y otros elementos se dividan entre páginas. Aplica configuraciones específicas
    para medios de impresión para asegurar un ajuste correcto al formato A4.

    Args:
        orientation (str): Orientación de la página

    Returns:
        CSS: Objeto CSS con los estilos necesarios
    """
    # Definir dimensiones basadas en la orientación
    if orientation == "portrait":
        width, height = "21cm", "29.7cm"
    else:  # landscape
        width, height = "29.7cm", "21cm"
        
    return CSS(
        string=f"""
        /* Configuración general de página */
        @page {{
            size: {width} {height};
            margin: 1.5cm 1.5cm 1.5cm 1.5cm;
            padding: 0;
            @bottom-center {{
                content: counter(page) "/" counter(pages);
                font-size: 9pt;
                margin-top: 0.8cm;
            }}
        }}
        
        /* Impedir que la página se rompa entre títulos y su contenido */
        @page no-blank {{
            size: {width} {height};
            margin: 1.5cm 1.5cm 1.5cm 1.5cm;
        }}
                
        /* Establecer el modelo de caja para todos los elementos */
        * {{
            box-sizing: border-box;
        }}
        
        /* Configuración básica del documento */
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            font-size: 12pt; /* Tamaño base de fuente para mejor legibilidad */
        }}
        
        /* Configuraciones para evitar saltos de página inapropiados */
        table {{
            page-break-inside: avoid;
            width: 100% !important;
            max-width: 100%;
            table-layout: fixed;
            border-collapse: collapse;
        }}
        
        /* SOLO forzar saltos de página después de elementos con estas clases específicas */
        .page-break-after {{
            page-break-after: always;
        }}
        
        /* Evitar TODOS los saltos después de encabezados y asegurar que se mantengan con su contenido */
        h1, h2, h3, h4, h5, h6 {{
            page-break-after: avoid !important;
            page-break-before: avoid !important;
            page-break-inside: avoid !important;
            margin-bottom: 0.5em;
            break-after: avoid !important; /* Propiedad moderna para evitar saltos */
            break-before: avoid !important;
            break-inside: avoid !important;
        }}
        
        /* Contenedores de títulos y su contenido */
        .titulo-seccion, .semana-titulo, .sesion-titulo,
        section, article, .container, .content-block, 
        header, .header, .title-container, .content {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            margin-bottom: 1em;
        }}
        
        /* Reglas específicas para semanas y sesiones */
        [class*="semana"], [class*="sesion"], 
        h1 + *, h2 + *, h3 + *, h4 + *, h5 + *, h6 + * {{
            page-break-before: avoid !important;
            break-before: avoid !important;
        }}
        
        /* Forzar que elementos después de títulos estén juntos */
        h1:not(:last-child), h2:not(:last-child), h3:not(:last-child),
        h4:not(:last-child), h5:not(:last-child), h6:not(:last-child) {{
            margin-bottom: 0;
        }}
        
        /* Establecer un tamaño mínimo de bloque para evitar espacios en blanco */
        .semana-container, .sesion-container, .ejercicio-container {{
            min-height: 4cm;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}
        
        /* Ajustes para listas y párrafos */
        p, ul, ol {{
            orphans: 3; /* Mínimo de líneas al final de una página */
            widows: 3;  /* Mínimo de líneas al inicio de una página */
        }}
        
        /* Asegurar que las imágenes no se dividan */
        img {{
            page-break-inside: avoid;
            max-width: 100%;
            height: auto;
        }}
        
        /* Ajustar celdas para mejor legibilidad */
        td, th {{
            word-wrap: break-word;
            overflow-wrap: break-word;
            padding: 5px;
        }}
        
        /* Asegurar que el contenido se ajuste a la página */
        html, body {{
            width: 100%;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
            height: auto !important; /* Evitar alturas fijas que generen espacios */
            min-height: 0 !important;
        }}
        
        /* Eliminar espacios en blanco innecesarios */
        * {{
            box-sizing: border-box;
        }}
        
        /* Utilizar floats de manera segura para impresión */
        .clearfix::after {{
            content: "";
            display: table;
            clear: both;
        }}
        
        /* Mejora para divs que contienen tablas o imágenes grandes */
        div {{
            max-width: 100%;
            overflow-x: hidden;
        }}
        
        /* Enfoque recomendado para mantener elementos juntos en WeasyPrint */
        h1, h2, h3, h4, h5, h6 {{
            break-after: auto !important;  /* Anular cualquier break-after */
            margin-bottom: 0.5em;
            margin-top: 1em;
            font-weight: bold;
            /* Agrupar visualmente los encabezados con su contenido */
            padding-bottom: 0.2em;
        }}
        
        /* Usar combinadores de adyacencia para conectar encabezados con contenido */
        h1 + p, h2 + p, h3 + p, h4 + p, h5 + p, h6 + p,
        h1 + div, h2 + div, h3 + div, h4 + div, h5 + div, h6 + div,
        h1 + table, h2 + table, h3 + table, h4 + table, h5 + table, h6 + table,
        h1 + ul, h2 + ul, h3 + ul, h4 + ul, h5 + ul, h6 + ul,
        h1 + ol, h2 + ol, h3 + ol, h4 + ol, h5 + ol, h6 + ol {{
            margin-top: 0 !important;
        }}
        
        /* Envolver encabezados con su contenido relacionado */
        div, section, article {{
            page-break-inside: auto;  /* Permitir divisiones de página dentro de secciones grandes */
        }}
        
        /* Aplicar solución conocida para encabezados de sesión y semana */
        [class*="semana"], [class*="sesion"] {{
            display: block;
            /* Garantizar que haya suficiente espacio para el contenido */
            page-break-inside: auto;
        }}
        
        /* Solución para tablas */
        table {{
            width: 100% !important;
            max-width: 100%;
            border-collapse: collapse;
            margin-top: 0.5em;
            margin-bottom: 1em;
        }}
        
        /* Contadores para controlar la altura máxima de los bloques */
        body {{
            counter-reset: page;
        }}
        
        /* Regla principal para evitar páginas en blanco tras encabezados */
        h1, h2, h3, h4, h5, h6 {{
            page: no-blank; /* Usar página nombrada para evitar páginas en blanco */
            margin-top: 1em; /* Espacio antes del encabezado */
            margin-bottom: 0.4em; /* Espacio mínimo tras el encabezado */
            page-break-after: avoid; /* Evitar salto tras encabezado */
        }}

        /* Envolver contenido del encabezado con su texto siguiente */
        h1, h2, h3, h4, h5, h6, p {{
            orphans: 2; /* Al menos 2 líneas al final de página */
            widows: 2;  /* Al menos 2 líneas al inicio de página */
        }}

        /* Solucionar problemas de posicionamiento */
        div {{
            position: relative !important; /* Evitar problemas de posicionamiento absoluto */
        }}
        
        /* Asegurar que las secciones con títulos tengan contenido mínimo */
        [id*="semana"], [id*="sesion"],
        [class*="semana"], [class*="sesion"] {{
            min-height: 4em; /* Alto mínimo para contenido */
            page-break-inside: auto; /* Permitir saltos dentro de secciones largas */
            display: block; /* Forzar display block */
        }}
        
        /* Ajustar imágenes */
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0.5em 0;
        }}
        
        /* Ajustar tablas */
        td, th {{
            padding: 4px;
            vertical-align: top;
            text-align: left;
        }}
        
        /* Regla para evitar que los títulos "semana" queden solos en páginas */
        .semana-titulo, .sesion-titulo,
        h1[id*="semana"], h2[id*="semana"],
        h1[class*="semana"], h2[class*="semana"],
        h1[id*="sesion"], h2[id*="sesion"],
        h1[class*="sesion"], h2[class*="sesion"] {{
            break-inside: avoid;
            break-after: avoid;
            display: inline-block;
            /* Conectar título con su contenido */
            margin-bottom: 0.1em;
            width: 100%;
        }}
        
        /* Envolver contenido del título */
        .semana-titulo + *, .sesion-titulo + *,
        h1[id*="semana"] + *, h2[id*="semana"] + *,
        h1[class*="semana"] + *, h2[class*="semana"] + *,
        h1[id*="sesion"] + *, h2[id*="sesion"] + *,
        h1[class*="sesion"] + *, h2[class*="sesion"] + * {{
            break-before: avoid;
            margin-top: 0;
            padding-top: 0.2em;
            display: inline-block;
            width: 100%;
        }}
        
        /* Crear estructura de bloques para títulos */
        h1, h2, h3 {{
            page-break-after: avoid;
            /* Forzar que cualquier elemento que siga al encabezado no se separe */
            display: block;
        }}
        
        h1 + *, h2 + *, h3 + * {{
            page-break-before: avoid;
        }}
        
        /* Estilos para resumen con contenido completo */
        h1[id*="resumen"], h2[id*="resumen"],
        h1[class*="resumen"], h2[class*="resumen"] {{
            /* Crear un grupo con su contenido siguiente */
            display: inline-block;
            page-break-inside: avoid;
            page-break-after: auto;
            margin-bottom: 0.2em;
            width: 100%;
        }}
    """
    )


def combine_documents_to_pdf(html_docs, output_filename, orientation):
    """
    Combina varios documentos HTML en un único PDF.

    Args:
        html_docs (list): Lista de objetos HTML
        output_filename (str): Ruta al archivo PDF de salida
        orientation (str): Orientación de la página

    Returns:
        bool: True si el proceso fue exitoso, False en caso contrario
    """
    # Seleccionar estilo según orientación
    page_style = STYLES[orientation]

    # Renderizar documentos
    rendered_docs = []
    for html_doc in html_docs:
        # Usar el mismo estilo de preservación para todos los documentos
        preserve_style = get_content_preservation_css(orientation)
        rendered_doc = html_doc.render(stylesheets=[preserve_style])
        rendered_docs.append(rendered_doc)

    # Si no hay documentos, salir
    if not rendered_docs:
        print("No se pudieron procesar documentos HTML.")
        return False

    # Extraer todas las páginas
    all_pages = []
    for doc in rendered_docs:
        all_pages.extend(doc.pages)

    if not all_pages:
        print("No hay páginas para escribir en el PDF.")
        return False

    # Crear PDF final
    print(f"Ensamblando el PDF final: {output_filename}...")
    rendered_docs[0].copy(all_pages).write_pdf(output_filename)
    print(
        f"\u00a1PDF '{output_filename}' creado exitosamente con {len(all_pages)} página(s)!"
    )
    return True


def cleanup_temp_files(temp_files, temp_dir):
    """
    Limpia los archivos temporales y el directorio usado durante el proceso.

    Args:
        temp_files (list): Lista de rutas a archivos temporales
        temp_dir (str): Ruta al directorio temporal
    """
    # Eliminar archivos temporales
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                print(
                    f"Advertencia: No se pudo eliminar el archivo temporal '{temp_file}': {e}"
                )

    # Eliminar directorio temporal
    try:
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
    except Exception as e:
        print(
            f"Advertencia: No se pudo eliminar el directorio temporal '{temp_dir}': {e}"
        )


# --- Funciones de gestión del historial ---
def load_history():
    """
    Carga el historial de rutas usadas previamente.

    Returns:
        dict: Diccionario con el historial o estructura vacía si no hay historial
    """
    # Crear directorio de configuración si no existe
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    # Cargar historial existente o crear uno nuevo
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Advertencia: No se pudo cargar el historial: {e}")

    # Devolver estructura vacía si no hay historial o hubo error
    return {"input_paths": []}


def save_history(history):
    """
    Guarda el historial de rutas usadas.

    Args:
        history (dict): Diccionario con el historial a guardar
    """
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Advertencia: No se pudo guardar el historial: {e}")


def update_input_history(path):
    """
    Actualiza el historial con una nueva ruta, manteniéndola al principio.

    Args:
        path (str): Ruta a añadir al historial
    """
    history = load_history()

    # Eliminar la ruta si ya existe en el historial
    if path in history["input_paths"]:
        history["input_paths"].remove(path)

    # Añadir la ruta al principio de la lista
    history["input_paths"].insert(0, path)

    # Mantener solo las últimas 3 rutas
    history["input_paths"] = history["input_paths"][:3]

    # Guardar el historial actualizado
    save_history(history)


def get_input_directory_with_history():
    """
    Solicita al usuario la ruta de entrada mostrando sugerencias del historial.

    Returns:
        str: Ruta seleccionada o ingresada por el usuario

    Raises:
        SystemExit: Si ocurre un error que impide continuar
    """
    try:
        history = load_history()
        input_paths = history.get("input_paths", [])

        if input_paths:
            # Mostrar historial de rutas recientes
            print("Rutas usadas recientemente:")
            for i, path in enumerate(input_paths, 1):
                print(f"  {i}. {path}")

            try:
                choice = input(
                    "\nSelecciona una ruta (1-3) o ingresa una nueva ruta: "
                ).strip()

                # Verificar si se seleccionó una ruta del historial
                if choice.isdigit() and 1 <= int(choice) <= len(input_paths):
                    return input_paths[int(choice) - 1]
                else:
                    # Si no es un número válido, tratar como una nueva ruta
                    return choice
            except EOFError:
                # En modo no interactivo, usar la primera ruta del historial
                print(f"\nUsando la ruta más reciente: {input_paths[0]}")
                return input_paths[0]
        else:
            # Sin historial, solicitar la ruta
            try:
                return input(
                    "Ingresa la ruta de la carpeta que contiene tus archivos HTML: "
                ).strip()
            except EOFError:
                print(
                    "\nError: No se pudo leer la entrada. Por favor, especifica la ruta con --input."
                )
                sys.exit(1)
    except Exception as e:
        print(f"Error al obtener el directorio de entrada: {e}")
        print("Por favor, especifica la ruta con --input.")
        sys.exit(1)


def parse_args():
    """
    Configura y procesa los argumentos de línea de comandos.

    Returns:
        argparse.Namespace: Objeto con los argumentos procesados
    """
    parser = argparse.ArgumentParser(
        description="Creador de PDF a partir de Múltiples Archivos HTML"
    )
    parser.add_argument(
        "-i", "--input", help="Ruta de la carpeta que contiene los archivos HTML"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Nombre del archivo PDF de salida (si no se especifica ruta, se guardará en la misma carpeta que los HTML)",
    )
    parser.add_argument(
        "-p",
        "--portrait",
        action="store_true",
        help="Usar orientación vertical (portrait) en lugar de apaisada (landscape)",
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Usar modo interactivo"
    )
    return parser.parse_args()


def show_welcome_message():
    """
    Muestra el mensaje de bienvenida al usuario.
    """
    print("--- Creador de PDF a partir de Múltiples Archivos HTML ---")
    print("Este script combina archivos HTML en una carpeta en un solo PDF.")
    print("Los archivos se ordenan numéricamente y mantienen su formato.")
    print("---------------------------------------------------------------------")


def get_input_parameters(args):
    """
    Obtiene los parámetros de entrada desde línea de comandos o modo interactivo.

    Args:
        args: Argumentos de línea de comandos

    Returns:
        tuple: (input_directory, output_pdf_name, page_orientation)
    """
    # Modo interactivo o sin especificar carpeta de entrada
    if args.interactive or not args.input:
        try:
            # Obtener directorio de entrada desde el historial
            input_directory = get_input_directory_with_history()

            # Buscar archivos HTML y usar el nombre del primero como base para el PDF
            html_files = find_html_files(input_directory)
            if html_files:
                # Tomar el nombre del primer archivo HTML y cambiar la extensión a .pdf
                first_file_name = os.path.basename(html_files[0])
                default_pdf_name = os.path.splitext(first_file_name)[0] + ".pdf"
                default_output = os.path.join(input_directory, default_pdf_name)
            else:
                # Si no hay archivos HTML, usar el nombre predeterminado
                default_output = os.path.join(input_directory, "output.pdf")

            output_prompt = (
                f"Nombre del PDF [predeterminado: {os.path.basename(default_output)}]: "
            )

            try:
                output_pdf_name = input(output_prompt).strip()
                if not output_pdf_name:
                    output_pdf_name = default_output
                elif not os.path.isabs(output_pdf_name) and not os.path.dirname(
                    output_pdf_name
                ):
                    output_pdf_name = os.path.join(input_directory, output_pdf_name)
            except EOFError:
                print(
                    f"\nUsando nombre predeterminado: {os.path.basename(default_output)}"
                )
                output_pdf_name = default_output

            # Preguntar por orientación
            try:
                choice = input("Orientación: (1 -> portrait, 2 -> landscape): ").strip()
                page_orientation = "portrait" if choice == "1" else "landscape"
            except EOFError:
                print("\nUsando orientación predeterminada: landscape")
                page_orientation = "landscape"

        except Exception as e:
            print(f"\nError en modo interactivo: {e}")
            print("Ejecutando en modo no interactivo con valores predeterminados.")

            if not args.input:
                print(
                    "Error: Se requiere especificar la carpeta de entrada con --input"
                )
                sys.exit(1)

            input_directory = args.input
            output_pdf_name = args.output or os.path.join(input_directory, "output.pdf")
            page_orientation = "portrait" if args.portrait else "landscape"
    else:
        # Modo no interactivo
        input_directory = args.input

        # Determinar archivo de salida
        if not args.output:
            # Buscar archivos HTML y usar el nombre del primero como base para el PDF
            html_files = find_html_files(input_directory)
            if html_files:
                # Tomar el nombre del primer archivo HTML y cambiar la extensión a .pdf
                first_file_name = os.path.basename(html_files[0])
                default_pdf_name = os.path.splitext(first_file_name)[0] + ".pdf"
                output_pdf_name = os.path.join(input_directory, default_pdf_name)
            else:
                # Si no hay archivos HTML, usar el nombre predeterminado
                output_pdf_name = os.path.join(input_directory, "output.pdf")

            print(f"No se especificó archivo de salida. Usando: {output_pdf_name}")
        else:
            output_pdf_name = args.output
            # Si solo es un nombre sin ruta, colocarlo en la carpeta de entrada
            if not os.path.isabs(output_pdf_name) and not os.path.dirname(
                output_pdf_name
            ):
                output_pdf_name = os.path.join(input_directory, output_pdf_name)

        # Determinar orientación
        page_orientation = "portrait" if args.portrait else "landscape"

    # Asegurar que el nombre termine en .pdf
    if not output_pdf_name.lower().endswith(".pdf"):
        output_pdf_name += ".pdf"

    return input_directory, output_pdf_name, page_orientation


def main():
    """
    Función principal del programa.
    """
    # Obtener argumentos
    args = parse_args()

    # Mostrar bienvenida
    show_welcome_message()

    # Obtener parámetros
    input_directory, output_pdf_name, orientation = get_input_parameters(args)

    # Mostrar información de la orientación seleccionada
    orientation_display = (
        "vertical (portrait)" if orientation == "portrait" else "apaisada (landscape)"
    )
    print(f"\nUsando orientación {orientation_display} para el PDF.")

    # Actualizar historial
    update_input_history(input_directory)

    # Crear PDF
    create_pdf_from_html_folder(input_directory, output_pdf_name, orientation)


if __name__ == "__main__":
    main()
