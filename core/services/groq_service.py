from groq import Groq
from django.conf import settings

# Creamos el cliente de Groq con nuestra API key
cliente = Groq(api_key=settings.GROQ_API_KEY)


def preguntar_al_asistente(mensaje, contexto=""):
    """
    Función principal para hablar con el asistente.
    - mensaje: lo que el usuario pregunta o pide
    - contexto: información adicional que el asistente necesita saber
    """

    # Aquí le decimos al asistente cómo debe comportarse
    sistema = """
    Eres un asistente personal inteligente llamado ARIA 
    (Asistente de Respuesta Inteligente Automatizada).
    
    Tu trabajo es:
    - Ayudar a gestionar correos electrónicos
    - Clasificar información importante
    - Crear resúmenes y reportes
    - Gestionar notas y recordatorios
    
    Siempre respondes en español, de forma clara y concisa.
    """

    # Si hay contexto adicional lo agregamos al sistema
    if contexto:
        sistema += f"\n\nContexto actual:\n{contexto}"

    # Llamamos a Groq
    respuesta = cliente.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": sistema},
            {"role": "user", "content": mensaje}
        ],
        temperature=0.7,
        max_tokens=1024
    )

    # Retornamos solo el texto de la respuesta
    return respuesta.choices[0].message.content


def clasificar_texto(texto, categorias):
    """
    Clasifica un texto dentro de las categorías dadas.
    - texto: el contenido a clasificar (un correo por ejemplo)
    - categorias: lista de categorías posibles
    """

    mensaje = f"""
    Clasifica el siguiente texto en UNA de estas categorías: {', '.join(categorias)}
    
    Texto:
    {texto}
    
    Responde SOLO con el nombre de la categoría, sin explicación.
    """

    respuesta = cliente.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": mensaje}
        ],
        temperature=0.1,
        max_tokens=50
    )

    return respuesta.choices[0].message.content.strip()
