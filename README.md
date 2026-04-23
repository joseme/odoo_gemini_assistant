# Gemini AI Assistant para Odoo 17

Asistente de IA integrado en Odoo 17 con chat flotante, reconocimiento de voz local y respuesta hablada.

## Características

- **Chat con Gemini**: Respuestas inteligentes sobre el uso de Odoo (soporta Gemini 2.0, 1.5, 2.5 Pro)
- **Input de voz (Vosk)**: Reconocimiento de voz local, sin enviar audio a servicios externos
- **Respuesta hablada (edge-tts)**: Voces neuronales de Microsoft Edge, gratis y de alta calidad
- **Contexto automático**: Detecta el módulo, modelo y registro que el usuario está viendo
- **Integración con Knowledge**: Busca artículos relevantes del módulo Knowledge de Odoo

## Requisitos

- Odoo 17
- Python 3.10+
- API Key de Google Gemini (obtener en https://aistudio.google.com/apikey)
- Modelo Vosk para el idioma deseado
- Docker (si Odoo está en contenedor)

## Modelos de Gemini disponibles

| Modelo | Velocidad | Costo |推荐| Notas |
|---|---|---|---|---|
| `gemini-2.0-flash-exp` | Rápido | $0.000075/token | ✅ | Mejor balance |
| `gemini-2.0-flash-lite` | Muy rápido | $0.000037/token | | Máxima economía |
| `gemini-1.5-flash` | Rápido | $0.000075/token | | Estable, bien probado |
| `gemini-2.5-pro` | Medio | $0.00125/token | | Mejor calidad |

## Instalación

### 1. Instalar dependencias Python

```bash
pip install google-generativeai vosk edge-tts
```

### 2. Descargar modelo Vosk

Modelo pequeño para español (~40MB, rápido):
```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.22.zip
unzip vosk-model-small-es-0.22.zip
```

Modelo grande para español (~1.5GB, mayor precisión):
```bash
wget https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip
unzip vosk-model-es-0.42.zip
```

### 3. Instalar el módulo

Copiar la carpeta `odoo_gemini_assistant` al directorio de addons de Odoo:

```bash
cp -r odoo_gemini_assistant /path/to/odoo/addons/
```

Actualizar la lista de apps en Odoo e instalar "Gemini AI Assistant".

### 4. Configurar

Ir a **Configuración > Gemini Assistant > Configuración** y completar:

| Campo | Descripción | Ejemplo |
|---|---|---|
| Asistente habilitado | Activar/desactivar el widget | ✓ |
| Gemini API Key | Tu API key de Google | `AIza...` |
| Modelo Gemini | Modelo a usar | `gemini-2.0-flash-exp` |
| Ruta del modelo Vosk | Path al modelo descargado | `/opt/vosk/vosk-model-small-es-0.22` |
| Voz TTS | Voz para edge-tts | `es-ES-AlvaroNeural` |

## Instalación con Docker

### Opción A: Montar modelo como volumen

```yaml
# docker-compose.yml
services:
  odoo:
    image: odoo:17
    volumes:
      - ./odoo_addons:/mnt/addons
      - ./vosk-model:/opt/vosk-model  # Montar modelo Vosk

volumes:
  vosk-model:
```

En la configuración de Odoo:
```
Vosk Model Path: /opt/vosk-model/vosk-model-small-es-0.22
```

### Opción B: Incluir modelo en el contenedor

```dockerfile
FROM odoo:17

RUN apt-get update && apt-get install -y wget unzip && \
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-es-0.22.zip && \
    unzip -q vosk-model-small-es-0.22.zip -d /opt/vosk/ && \
    rm vosk-model-small-es-0.22.zip

COPY odoo_addons /mnt/addons
```

### Opción C: Descarga automática

El servicio puede descargar el modelo dinámicamente si no existe (configurable).

## Voces TTS disponibles

Algunas voces en español:

| Voz | Idioma | Género |
|---|---|---|
| `es-ES-AlvaroNeural` | Español (España) | Masculino |
| `es-ES-ElviraNeural` | Español (España) | Femenino |
| `es-MX-DaliaNeural` | Español (México) | Femenino |
| `es-MX-JorgeNeural` | Español (México) | Masculino |
| `es-AR-TomiNeural` | Español (Argentina) | Masculino |
| `es-CO-GonzaloNeural` | Español (Colombia) | Masculino |

Voces completas: https://github.com/rany2/edge-tts#available-voices

## Estructura del módulo

```
odoo_gemini_assistant/
├── __manifest__.py
├── __init__.py
├── requirements.txt
├── README.md
├── controllers/
│   ├── __init__.py
│   └── main.py              # Endpoints REST
├── models/
│   ├── __init__.py
│   └── gemini_config.py     # Configuración en res.config.settings
├── services/
│   ├── __init__.py
│   ├── gemini_service.py    # Wrapper de Gemini API
│   ├── vosk_service.py      # Speech-to-Text con Vosk
│   └── tts_service.py       # Text-to-Speech con edge-tts
├── static/src/
│   ├── js/chat_widget.js    # Componente OWL
│   ├── xml/chat_widget.xml  # Templates OWL
│   └── scss/chat_widget.scss # Estilos
└── views/
    ├── gemini_config_views.xml
    └── assets.xml
```

## Endpoints

| Endpoint | Tipo | Función |
|---|---|---|
| `/gemini_assistant/config` | JSON | Obtener configuración activa |
| `/gemini_assistant/chat` | JSON | Enviar mensaje y recibir respuesta |
| `/gemini_assistant/stt` | JSON | Transcribir audio a texto |
| `/gemini_assistant/tts` | HTTP | Generar audio MP3 desde texto |

## Uso del widget

1. El widget aparece como un botón flotante en la esquina inferior derecha
2. Click para abrir el chat
3. Escribir una pregunta o usar el micrófono para hablar
4. Cada respuesta del asistente tiene un botón de altavoz para escucharla

## Privacidad

- **Vosk**: El audio se procesa localmente en el servidor Odoo, nunca se envía a servicios externos
- **Gemini**: Solo se envía el texto transcrito y el contexto (módulo, modelo, registro)
- **edge-tts**: El audio se genera en el servidor y se envía al navegador

## Solución de problemas

### "Model not found" en Vosk
- Verificar que la ruta del modelo sea correcta
- Asegurarse de que el modelo esté descomprimido (contiene archivos `.json`, `.mdl`, etc.)

### Error de autenticación con Gemini
- Verificar que la API key sea válida
- Revisar que el proyecto de Google Cloud tenga habilitada la API de Gemini

### El micrófono no funciona
- Verificar permisos del navegador
- Usar HTTPS (requerido para MediaRecorder en Chrome)

## Licencia

LGPL-3
