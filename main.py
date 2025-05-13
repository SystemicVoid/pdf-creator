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
            with open(history_file, 'r') as f:
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
        with open(history_file, 'w') as f:
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
                choice = input("\nSelecciona una ruta (1-3) o ingresa una nueva ruta: ").strip()
                
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
                return input("Ingresa la ruta de la carpeta que contiene tus archivos HTML: ").strip()
            except EOFError:
                # Si hay un error EOF y no hay historial, usar una ruta predeterminada
                print("\nError: No se pudo leer la entrada. Por favor, especifica la ruta con --input.")
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
        "-o", "--output", 
        help="Nombre del archivo PDF de salida. Si no se especifica una ruta, se guardará en la misma carpeta que los archivos HTML"
    )
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
            elif not os.path.isabs(output_pdf_name) and not os.path.dirname(output_pdf_name):
                output_pdf_name = os.path.join(input_directory, output_pdf_name)
            
            # Preguntar por la orientación
            try:
                orientation_choice = input(
                    "Selecciona la orientación de página (1 para vertical/portrait, 2 para apaisada/landscape): "
                ).strip()
            except EOFError:
                print("\nUsando orientación predeterminada: apaisada (landscape)")
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
                print("Error: Se requiere especificar la carpeta de entrada con --input")
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
            if not os.path.isabs(output_pdf_name) and not os.path.dirname(output_pdf_name):
                output_pdf_name = os.path.join(input_directory, output_pdf_name)
        
        # Usar la orientación de los argumentos de línea de comandos
        page_orientation = "portrait" if args.portrait else "landscape"

    # Asegurar que el nombre del archivo termine en .pdf
    if not output_pdf_name.lower().endswith(".pdf"):
        output_pdf_name += ".pdf"

    # Mostrar la orientación seleccionada
    orientation_display = "vertical (portrait)" if page_orientation == "portrait" else "apaisada (landscape)"
    print(f"\nUsando orientación {orientation_display} para el PDF.")

    # Actualizar el historial con la ruta de entrada usada
    update_input_history(input_directory)
    
    # Crear el PDF a partir de los archivos HTML
    create_pdf_from_html_folder(input_directory, output_pdf_name, page_orientation)
