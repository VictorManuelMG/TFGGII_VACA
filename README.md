# 🐄 Programa VACA (Voice-Assisted Computer Accessibility)

**VACA** es un sistema de asistencia diseñado para facilitar el uso del ordenador a personas con movilidad reducida. Basado principalmente en tecnologías **CUA** (Computer Use Agents), su propósito es crear un agente inteligente capaz de **controlar un ordenador** mediante **prompts de voz** y, opcionalmente, **prompts escritos**.

## 🚀 Objetivo

Permitir la interacción con interfaces gráficas mediante lenguaje natural, utilizando inteligencia artificial para:

- Detectar y describir elementos en pantalla.
- Interpretar comandos de voz.
- Tomar decisiones contextuales.
- Simular acciones de usuario como clics o escritura.

---

## 🧠 Componentes del Sistema

El agente VACA se apoya en diversos modelos de inteligencia artificial, cada uno con una función específica:

### 🔍 Modelos Multimodales

> Actúan como el **cerebro** del sistema, combinando visión y lenguaje para razonamiento contextual.

- **Claude**
- **GPT**

> (ℹ) También se puede llegar a usar cualquier otro modelo multimodal que pueda entender imagenes.

### 🖼️ Detección y Descripción Visual

> Para reconocer y comprender los elementos en pantalla (iconos, botones, menús, etc.)

- **YOLO** – Detección de objetos e iconos en tiempo real.
- **FlorenceV2** – Generación de descripciones para los objetos detectados por YOLO.

### 🗣️ Reconocimiento y Síntesis de Voz (ASR/TTS)

> Para convertir voz a texto (_Speech-To-Text_) y texto a voz (_Text-To-Speech_).

- **Whisper** – Reconocimiento de voz (STT).
- **Coqui** – Síntesis de voz (TTS).

### 🌐 Navegación web

> Para realizar una navegación adecuada, usualmente se utilizara la biblioteca de browser use, pero el propio agente tambien puede realizar las tareas de navegacion con sus modelos implementados.

- **Browser Use**
- **Herramientas propias**

---
# Diagrama simple del funcionamiento:

![Diagrama CUA](assets/CUA%20FLOW.png)

---

# Ejemplo de captación del interfaz :


| GUI VACA | Imagen original | Resultado final |
|:--------:|:----------------:|:----------------:|
| ![GUI VACA](assets/GUI_inicial.png) | ![Imagen original](assets/ejemplo_original.jpeg) | ![Prompt y respuesta](assets/resultado_final.png) |

>Procesamiento con VACA

| Pensamiento 1 | Pensamiento 2 | Imagen YOLO |
|:-------------:|:-------------:|:-----------:|
| ![Pensamiento 1](assets/Pensamientos_1.png) | ![Pensamiento 2](assets/Pensamientos_2.png) | ![YOLO](assets/ejemplo_yoloed.jpeg) |

