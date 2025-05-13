#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import tempfile
import json
from weasyprint import HTML, CSS
from weasyprint.document import (
    Document,
)  # Para combinar páginas de múltiples fuentes HTML

# --- Hojas de Estilos CSS para la Página ---
# Estas hojas de estilos se aplicarán a cada documento HTML antes de renderizar sus páginas.
# Definen el tamaño de página como A4 (apaisado o vertical) y establecen márgenes.
LANDSCAPE_PAGE_STYLE = CSS(string="@page { size: A4 landscape; margin: 1cm; }")
PORTRAIT_PAGE_STYLE = CSS(string="@page { size: A4 portrait; margin: 1cm; }")

# Hoja de estilo mínima para medir el tamaño natural del contenido
MEASURE_STYLE = CSS(string="@page { size: auto; margin: 0; }")

# Por defecto usamos apaisado (landscape)
DEFAULT_PAGE_STYLE = LANDSCAPE_PAGE_STYLE


def natural_sort_key(s):
    """
    Función auxiliar para ordenar cadenas que contienen números de forma natural.
    Por ejemplo: ['sesion1.html', 'sesion2.html', 'sesion10.html'] en lugar de
    ['sesion1.html', 'sesion10.html', 'sesion2.html'].
    """
    import re
    # Dividir la cadena en segmentos numéricos y no numéricos
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]


def find_html_files(folder_path):
    """
    Encuentra todos los archivos .html en la carpeta especificada.
    Los archivos se devuelven ordenados numéricamente para un procesamiento consistente
    (por ejemplo, sesion1.html, sesion2.html, ..., sesion10.html, en lugar de
    ordenarlos alfabéticamente, lo que pondría sesion10.html antes que sesion2.html).

    Args:
        folder_path (str): La ruta a la carpeta que contiene los archivos HTML.

    Returns:
        list: Una lista de rutas a los archivos HTML encontrados, o una lista vacía.
    """
    search_path = os.path.join(folder_path, "*.html")
    # Usar ordenamiento natural para manejar correctamente archivos con números
    html_files = sorted(glob.glob(search_path), key=natural_sort_key)

    if not html_files:
        print(
            f"Advertencia: No se encontraron archivos .html en la carpeta: {folder_path}"
        )
    return html_files


# Esta función se ha incorporado directamente en create_pdf_from_html_folder para simplificar el código


def create_pdf_from_html_folder(
    input_folder, output_pdf_filename, orientation="landscape"
):
    """
    Crea un único archivo PDF a partir de todos los archivos HTML encontrados en una carpeta.
    Preserva el contenido completo de cada archivo HTML, permitiendo que fluya naturalmente a través
    de múltiples páginas si es necesario, mientras asegura que las tablas y otros elementos
    no se dividan entre páginas.

    Args:
        input_folder (str): La ruta a la carpeta que contiene los archivos HTML.
        output_pdf_filename (str): El nombre del archivo PDF de salida.
        orientation (str): Orientación de la página, "landscape" (apaisado) o "portrait" (vertical).
    """
    if not os.path.isdir(input_folder):
        print(
            f"Error: La carpeta de entrada '{input_folder}' no existe o no es un directorio."
        )
        return

    html_files = find_html_files(input_folder)
    if not html_files:
        print("No hay archivos HTML para procesar. Saliendo.")
        return

    print(f"Archivos HTML encontrados para procesar (en orden): {html_files}")

    # Crear directorio temporal para PDFs individuales
    temp_dir = tempfile.mkdtemp(prefix="pdf_creator_")
    temp_pdf_files = []

    # Lista para almacenar documentos HTML
    all_html_docs = []

    try:
        for i, html_file in enumerate(html_files):
            print(f"Procesando archivo: {html_file}...")

            # Crear un archivo PDF temporal para este archivo HTML
            temp_pdf = os.path.join(temp_dir, f"doc_{i}.pdf")
            temp_pdf_files.append(temp_pdf)

            # Crear un estilo CSS personalizado que preserve el contenido completo
            # y asegure que las tablas y otros elementos no se dividan entre páginas
            preserve_content_style = CSS(
                string=f"""
                @page {{
                    size: A4 {orientation};
                    margin: 1cm;
                }}
                
                /* Evitar que las tablas se dividan entre páginas */
                table {{
                    page-break-inside: avoid;
                }}
                
                /* Evitar que los encabezados se separen del contenido siguiente */
                h1, h2, h3, h4, h5, h6 {{
                    page-break-after: avoid;
                }}
                
                /* Asegurar que las imágenes no se dividan */
                img {{
                    page-break-inside: avoid;
                }}
                
                /* Ajustar el ancho de las tablas para que quepan en la página */
                table {{
                    width: 100% !important;
                    max-width: 100%;
                    table-layout: fixed;
                }}
                
                /* Ajustar el tamaño de las celdas para mejor legibilidad */
                td, th {{
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }}
            """
            )

            # Convertir el HTML a PDF preservando todo el contenido
            html_doc = HTML(filename=html_file, base_url=input_folder)
            html_doc.write_pdf(temp_pdf, stylesheets=[preserve_content_style])

            print(
                f"'{html_file}' procesado y guardado temporalmente como '{temp_pdf}'."
            )

            # Guardar el documento HTML para combinar posteriormente
            all_html_docs.append(html_doc)

        # Renderizar todos los documentos HTML con el estilo de preservación de contenido
        all_documents = []
        for i, html_doc in enumerate(all_html_docs):
            # Seleccionar el estilo de página según la orientación
            page_style = (
                PORTRAIT_PAGE_STYLE
                if orientation == "portrait"
                else LANDSCAPE_PAGE_STYLE
            )

            # Crear un estilo CSS personalizado para este documento
            preserve_content_style = CSS(
                string=f"""
                @page {{
                    size: A4 {orientation};
                    margin: 1cm;
                }}
                
                /* Evitar que las tablas se dividan entre páginas */
                table {{
                    page-break-inside: avoid;
                }}
                
                /* Evitar que los encabezados se separen del contenido siguiente */
                h1, h2, h3, h4, h5, h6 {{
                    page-break-after: avoid;
                }}
            """
            )

            # Renderizar el documento con el estilo de preservación
            document = html_doc.render(stylesheets=[preserve_content_style])
            all_documents.append(document)

        # Combinar todas las páginas en un solo documento
        if all_documents:
            all_pages = []
            for doc in all_documents:
                all_pages.extend(doc.pages)

            if all_pages:
                # Usar el primer documento como base
                print(f"Ensamblando el PDF final: {output_pdf_filename}...")
                all_documents[0].copy(all_pages).write_pdf(output_pdf_filename)
                print(
                    f"\u00a1PDF '{output_pdf_filename}' creado exitosamente con {len(all_pages)} página(s)!"
                )
            else:
                print("No hay páginas para escribir en el PDF.")
        else:
            print("No se pudieron procesar documentos HTML.")

    except Exception as e:
        print(f"Error al escribir el archivo PDF final '{output_pdf_filename}': {e}")
    finally:
        # Limpiar archivos temporales
        for temp_file in temp_pdf_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(
                        f"Advertencia: No se pudo eliminar el archivo temporal '{temp_file}': {e}"
                    )

        # Eliminar el directorio temporal
        try:
            os.rmdir(temp_dir)
        except Exception as e:
            print(
                f"Advertencia: No se pudo eliminar el directorio temporal '{temp_dir}': {e}"
            )


def load_history():
    """Cargar el historial de rutas usadas anteriormente"""
    config_dir = os.path.expanduser("~/.config/pdf-creator")
    history_file = os.path.join(config_dir, "history.json")

    # Crear directorio de configuración si no existe
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)

    # Cargar historial existente o crear uno nuevo
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Advertencia: No se pudo cargar el historial: {e}")

    # Devolver estructura vacía si no hay historial o hubo error
    return {"input_paths": []}


def save_history(history):
    """Guardar el historial de rutas usadas"""
    config_dir = os.path.expanduser("~/.config/pdf-creator")
    history_file = os.path.join(config_dir, "history.json")

    try:
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Advertencia: No se pudo guardar el historial: {e}")


def update_input_history(path):
    """Actualizar el historial de rutas de entrada"""
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
    """Solicitar la ruta de entrada con sugerencias del historial"""
    try:
        history = load_history()
        input_paths = history.get("input_paths", [])

        if input_paths:
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
                # Si hay un error EOF, usar la primera ruta del historial
                print(f"\nUsando la ruta más reciente: {input_paths[0]}")
                return input_paths[0]
        else:
            # Si no hay historial, simplemente solicitar la ruta
            try:
                return input(
                    "Ingresa la ruta de la carpeta que contiene tus archivos HTML: "
                ).strip()
            except EOFError:
                # Si hay un error EOF y no hay historial, usar una ruta predeterminada
                print(
                    "\nError: No se pudo leer la entrada. Por favor, especifica la ruta con --input."
                )
                sys.exit(1)
    except Exception as e:
        print(f"Error al obtener el directorio de entrada: {e}")
        print("Por favor, especifica la ruta con --input.")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    import argparse

    # Configurar el parser de argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description="Creador de PDF a partir de Múltiples Archivos HTML"
    )
    parser.add_argument(
        "-i", "--input", help="Ruta de la carpeta que contiene los archivos HTML"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Nombre del archivo PDF de salida. Si no se especifica una ruta, se guardará en la misma carpeta que los archivos HTML",
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
    args = parser.parse_args()

    print("--- Creador de PDF a partir de Múltiples Archivos HTML (Linux) ---")
    print("Este script toma todos los archivos .html de una carpeta especificada,")
    print("los ordena alfabéticamente y los une en un solo archivo PDF.")
    print("Cada archivo HTML se renderizará, por defecto, en formato A4 apaisado.\n")
    print("\n---------------------------------------------------------------------\n")

    # Determinar si usar modo interactivo o argumentos de línea de comandos
    if args.interactive or (not args.input):
        try:
            # Modo interactivo con historial
            input_directory = get_input_directory_with_history()

            # Sugerir un nombre de archivo por defecto en la misma carpeta
            default_output_name = os.path.join(input_directory, "output.pdf")
            output_prompt = f"Ingresa el nombre para el archivo PDF de salida [predeterminado: {default_output_name}]: "

            try:
                output_pdf_name = input(output_prompt).strip()
            except EOFError:
                print(f"\nUsando nombre predeterminado: {default_output_name}")
                output_pdf_name = ""

            # Si no se proporciona un nombre, usar el predeterminado
            if not output_pdf_name:
                output_pdf_name = default_output_name
            # Si solo se proporciona un nombre sin ruta, colocarlo en la carpeta de entrada
            elif not os.path.isabs(output_pdf_name) and not os.path.dirname(
                output_pdf_name
            ):
                output_pdf_name = os.path.join(input_directory, output_pdf_name)

            # Preguntar por la orientación
            try:
                orientation_choice = input(
                    "Orientación: (1 -> portrait, 2 -> landscape): "
                ).strip()
            except EOFError:
                print("\nUsando orientación predeterminada: landscape")
                orientation_choice = "2"

            # Determinar la orientación basada en la elección del usuario
            page_orientation = "portrait" if orientation_choice == "1" else "landscape"
        except Exception as e:
            print(f"\nError en modo interactivo: {e}")
            print("Ejecutando en modo no interactivo con valores predeterminados.")

            # Usar valores predeterminados o argumentos de línea de comandos si están disponibles
            if args.input:
                input_directory = args.input
            else:
                print(
                    "Error: Se requiere especificar la carpeta de entrada con --input"
                )
                sys.exit(1)

            if args.output:
                output_pdf_name = args.output
            else:
                output_pdf_name = os.path.join(input_directory, "output.pdf")

            page_orientation = "portrait" if args.portrait else "landscape"
    else:
        # Modo no interactivo (argumentos de línea de comandos)
        if not args.input:
            print("Error: Se requiere especificar la carpeta de entrada con --input")
            sys.exit(1)

        input_directory = args.input

        # Si no se especifica un archivo de salida, usar uno predeterminado en la misma carpeta
        if not args.output:
            output_pdf_name = os.path.join(input_directory, "output.pdf")
            print(f"No se especificó archivo de salida. Usando: {output_pdf_name}")
        else:
            output_pdf_name = args.output
            # Si solo se proporciona un nombre sin ruta, colocarlo en la carpeta de entrada
            if not os.path.isabs(output_pdf_name) and not os.path.dirname(
                output_pdf_name
            ):
                output_pdf_name = os.path.join(input_directory, output_pdf_name)

        # Usar la orientación de los argumentos de línea de comandos
        page_orientation = "portrait" if args.portrait else "landscape"

    # Asegurar que el nombre del archivo termine en .pdf
    if not output_pdf_name.lower().endswith(".pdf"):
        output_pdf_name += ".pdf"

    # Mostrar la orientación seleccionada
    orientation_display = (
        "vertical (portrait)"
        if page_orientation == "portrait"
        else "apaisada (landscape)"
    )
    print(f"\nUsando orientación {orientation_display} para el PDF.")

    # Actualizar el historial con la ruta de entrada usada
    update_input_history(input_directory)

    # Crear el PDF a partir de los archivos HTML
    create_pdf_from_html_folder(input_directory, output_pdf_name, page_orientation)
