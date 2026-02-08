""" 
Defines available models for the chat service 

"""

AVAILABLE_MODELS = [
    {'id': 'gemma3:1b', 'name': 'Gemma 3', 'description': 'Fast & efficient', 'size': '1B'},
    {'id': 'qwen2.5:3b', 'name': 'qwen 2.5', 'description': 'Balanced performance', 'size': '3B'},
]

DEFAULT_MODEL = AVAILABLE_MODELS[0]
