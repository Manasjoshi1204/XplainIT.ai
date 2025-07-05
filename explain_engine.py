import openai

# 🌐 OpenRouter / OpenAI setup
client = openai.OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

def generate_explanation(topic, level, tone, extras, language):
    prompt = f"""
Explain the topic or code: "{topic}".
- Understanding level: {level}
- Tone: {tone}
- Extras: {extras}
- Preferred language: {language or 'English'}
Ensure clarity, accuracy, and readability.
"""
    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"
