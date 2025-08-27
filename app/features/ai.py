
from g4f.client import Client


def get_ai_response(query, message_history=None, brain_context=None):
    """Get response from the AI model."""
    if message_history is None:
        message_history = []

    system_message = {"role": "system", "content": "You are a helpful assistant."}
    if brain_context:
        system_message["content"] = brain_context

    # Prepend system message if not already there or if it's different
    if not message_history or message_history[0]['role'] != 'system':
         messages = [system_message] + message_history + [{"role": "user", "content": query}]
    else:
         # Update system message if it's different
         if message_history[0]['content'] != system_message['content']:
             message_history[0] = system_message
         messages = message_history + [{"role": "user", "content": query}]


    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"
