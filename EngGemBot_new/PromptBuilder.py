class PromptBuilder:
    @staticmethod
    def simplePrompt():
        return (
            "Згенеруй 5 карток для вивчення англійської мови. "
            "Поверни ТІЛЬКИ чистий JSON-масив без жодного додаткового тексту, "
            "пояснень чи Markdown-форматування. "
            "Структура: [{'question': 'word', 'answer': 'переклад'}, ...]"
        )
