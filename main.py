#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
from weasyprint import HTML, CSS
from weasyprint.document import (
    Document,
)  # Para combinar páginas de múltiples fuentes HTML

# --- Hojas de Estilos CSS para la Página ---
# Estas hojas de estilos se aplicarán a cada documento HTML antes de renderizar sus páginas.
# Definen el tamaño de página como A4 (apaisado o vertical) y establecen márgenes.
LANDSCAPE_PAGE_STYLE = CSS(string="@page { size: A4 landscape; margin: 1cm; }")
PORTRAIT_PAGE_STYLE = CSS(string="@page { size: A4 portrait; margin: 1cm; }")

# Por defecto usamos apaisado (landscape)
DEFAULT_PAGE_STYLE = LANDSCAPE_PAGE_STYLE


def find_html_files(folder_path):
    """
    Encuentra todos los archivos .html en la carpeta especificada.
    Los archivos se devuelven ordenados alfabéticamente para un procesamiento consistente.

    Args:
        folder_path (str): La ruta a la carpeta que contiene los archivos HTML.

    Returns:
        list: Una lista de rutas a los archivos HTML encontrados, o una lista vacía.
    """
    search_path = os.path.join(folder_path, "*.html")
    html_files = sorted(glob.glob(search_path))

    if not html_files:
        print(
            f"Advertencia: No se encontraron archivos .html en la carpeta: {folder_path}"
        )
    return html_files


def create_pdf_from_html_folder(input_folder, output_pdf_filename, orientation="landscape"):
    """
    Crea un único archivo PDF a partir de todos los archivos HTML encontrados en una carpeta.
    El contenido de cada archivo HTML se añade secuencialmente al PDF.
    Se aplica un estilo de página A4 apaisado por defecto.

    Args:
        input_folder (str): La ruta a la carpeta que contiene los archivos HTML.
        output_pdf_filename (str): El nombre del archivo PDF de salida.
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

    # Enfoque alternativo: crear un PDF por cada HTML y luego combinarlos
    # usando una herramienta externa o biblioteca como PyPDF2
    temp_pdf_files = []

    # Seleccionar el estilo de página según la orientación
    page_style = PORTRAIT_PAGE_STYLE if orientation == "portrait" else LANDSCAPE_PAGE_STYLE
    
    try:
        # Crear PDF individuales para cada archivo HTML
        for html_file_path in html_files:
            print(f"Procesando archivo: {html_file_path}...")
            try:
                # Crear un nombre de archivo temporal para este PDF
                temp_pdf_path = f"{os.path.splitext(html_file_path)[0]}_temp.pdf"
                temp_pdf_files.append(temp_pdf_path)

                # Renderizar el HTML a PDF
                doc_html_source = HTML(filename=html_file_path, base_url=input_folder)
                doc_html_source.write_pdf(
                    temp_pdf_path, stylesheets=[page_style]
                )
                print(
                    f"'{html_file_path}' procesado y guardado temporalmente como '{temp_pdf_path}'."
                )

            except Exception as e:
                print(f"Error procesando el archivo '{html_file_path}': {e}")
                print("Saltando este archivo y continuando con el siguiente.")
                continue

        if not temp_pdf_files:
            print("No se pudieron crear PDFs temporales. No se generará el PDF final.")
            return

        # Ahora combinamos todos los PDFs en uno solo usando el método de WeasyPrint
        print(f"Ensamblando el PDF final: {output_pdf_filename}...")

        # Usamos el primer PDF como base y añadimos el resto como páginas adicionales
        all_html_docs = []
        for html_file in html_files:
            html_doc = HTML(filename=html_file, base_url=input_folder)
            all_html_docs.append(html_doc)

        # Renderizar todos los documentos HTML
        all_rendered = [
            doc.render(stylesheets=[page_style]) for doc in all_html_docs
        ]

        # Extraer todas las páginas
        all_pages = []
        for doc in all_rendered:
            all_pages.extend(doc.pages)

        # Crear un nuevo documento con todas las páginas
        if all_pages:
            # Usar el primer documento renderizado como base
            all_rendered[0].copy(all_pages).write_pdf(output_pdf_filename)
            print(
                f"¡PDF '{output_pdf_filename}' creado exitosamente con {len(all_pages)} página(s)!"
            )
        else:
            print("No hay páginas para escribir en el PDF.")

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
    parser.add_argument("-o", "--output", help="Nombre del archivo PDF de salida")
    parser.add_argument(
        "-p", "--portrait", action="store_true", 
        help="Usar orientación vertical (portrait) en lugar de apaisada (landscape)"
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
    if args.interactive or (not args.input and not args.output):
        # Modo interactivo
        input_directory = input(
            "Ingresa la ruta de la carpeta que contiene tus archivos HTML: "
        ).strip()
        output_pdf_name = input(
            "Ingresa el nombre para el archivo PDF de salida (ej. plan_completo.pdf): "
        ).strip()
        
        # Preguntar por la orientación
        orientation_choice = input(
            "Selecciona la orientación de página (1 para vertical/portrait, 2 para apaisada/landscape): "
        ).strip()
        
        # Determinar la orientación basada en la elección del usuario
        page_orientation = "portrait" if orientation_choice == "1" else "landscape"
    else:
        # Modo no interactivo (argumentos de línea de comandos)
        if not args.input:
            print("Error: Se requiere especificar la carpeta de entrada con --input")
            sys.exit(1)
        if not args.output:
            print("Error: Se requiere especificar el archivo de salida con --output")
            sys.exit(1)

        input_directory = args.input
        output_pdf_name = args.output
        # Usar la orientación de los argumentos de línea de comandos
        page_orientation = "portrait" if args.portrait else "landscape"

    # Asegurar que el nombre del archivo termine en .pdf
    if not output_pdf_name.lower().endswith(".pdf"):
        output_pdf_name += ".pdf"

    # Mostrar la orientación seleccionada
    orientation_display = "vertical (portrait)" if page_orientation == "portrait" else "apaisada (landscape)"
    print(f"\nUsando orientación {orientation_display} para el PDF.")

    # Crear el PDF
    create_pdf_from_html_folder(input_directory, output_pdf_name, page_orientation)
