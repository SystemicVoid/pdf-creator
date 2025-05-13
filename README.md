# PDF Creator

Una herramienta para combinar múltiples archivos HTML en un único PDF con formato consistente y optimizado.

## Descripción

PDF Creator es una utilidad de línea de comandos que toma todos los archivos HTML de una carpeta especificada, los ordena correctamente y los combina en un único archivo PDF. Cada archivo HTML se renderiza con un formato consistente, permitiendo elegir entre orientación vertical (portrait) u horizontal (landscape) y preservando la integridad del contenido.

Esta herramienta es ideal para:
- Crear manuales o documentación a partir de páginas HTML
- Generar informes combinando múltiples fuentes HTML
- Archivar contenido web en formato PDF
- Crear materiales de formación o educativos

## Características

- Combina múltiples archivos HTML en un único PDF
- Ordenamiento natural de archivos (ej: sesion1.html, sesion2.html, sesion10.html)
- Preservación del contenido a través de múltiples páginas
- Evita división de tablas, imágenes y encabezados entre páginas
- Permite elegir entre orientación vertical (portrait) u horizontal (landscape)
- Recuerda las últimas 3 carpetas utilizadas
- Funciona en modo interactivo o con argumentos de línea de comandos
- Limpia automáticamente los archivos temporales
- Proporciona mensajes claros sobre el progreso y los errores

## Requisitos

- Python 3.12 o superior
- [uv](https://github.com/astral-sh/uv) - Gestor de paquetes y entornos virtuales
- Dependencias del sistema para WeasyPrint (ver sección de instalación)
- Espacio para archivos de configuración (~/.config/pdf-creator/)

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/pdf-creator.git
cd pdf-creator
```

### 2. Instalar dependencias del sistema para WeasyPrint

En sistemas basados en Debian/Ubuntu (incluido Pop!_OS):

```bash
sudo apt-get update
sudo apt-get install libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info
```

### 3. Configurar el entorno virtual con uv

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Uso

### Modo interactivo

```bash
uv run main.py --interactive
```

Esto te guiará a través de una serie de preguntas para especificar:
- La carpeta que contiene tus archivos HTML (mostrando las últimas 3 carpetas utilizadas)
- El nombre del archivo PDF de salida
- La orientación de página (vertical u horizontal)

### Modo línea de comandos

```bash
uv run main.py --input "/ruta/a/carpeta/html" --output nombre-archivo.pdf [--portrait]
```

Argumentos:
- `--input` o `-i`: Ruta a la carpeta que contiene los archivos HTML
- `--output` o `-o`: Nombre del archivo PDF de salida
- `--portrait` o `-p`: (Opcional) Usar orientación vertical en lugar de apaisada
- `--interactive`: Activar el modo interactivo

### Ejemplos

```bash
# Crear un PDF en orientación horizontal (predeterminada)
uv run main.py --input "./mis_archivos_html" --output documento.pdf

# Crear un PDF en orientación vertical
uv run main.py --input "./mis_archivos_html" --output documento.pdf --portrait

# Modo interactivo
uv run main.py --interactive
```

## Detalles técnicos

### Ordenamiento natural

A diferencia de la ordenación alfabética estándar, el ordenamiento natural maneja correctamente archivos con componentes numéricos:

- Ordenación estándar: `sesion1.html, sesion10.html, sesion2.html...`
- Ordenación natural: `sesion1.html, sesion2.html, ..., sesion10.html...`

Esto garantiza que los documentos aparezcan en el PDF en el orden lógico esperado.

### Preservación de contenido

La herramienta utiliza estilos CSS avanzados para:

- Evitar que las tablas se dividan entre páginas
- Mantener los encabezados con su contenido asociado
- Evitar la división de imágenes
- Optimizar el diseño de tablas para mayor legibilidad

### Historial de rutas

Las últimas tres carpetas utilizadas se guardan en `~/.config/pdf-creator/history.json`.

## Desarrollo

Para contribuir al desarrollo:

```bash
# Instalar dependencias de desarrollo
uv add --dev black

# Formatear código
uv run -m black .
```

### Estructura del código

El código está organizado en módulos funcionales:

- Funciones de utilidad (ordenamiento natural, búsqueda de archivos)
- Gestión del historial de rutas
- Procesamiento de PDF y renderizado
- Interfaz de línea de comandos

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## Agradecimientos

- [WeasyPrint](https://weasyprint.org/) - La biblioteca que hace posible la conversión de HTML a PDF
- [uv](https://github.com/astral-sh/uv) - Gestor de paquetes y entornos virtuales para Python
