import ollama
from typing import List, Dict, Any

class AIService:
    """
    Handles local AI inference using Ollama for Census data analysis.
    Ensures data privacy by keeping all processing local to the Diocese servers.
    """
    def __init__(self, model: str = "llama3"):
        self.model = model

    async def generate_census_summary(self, data: List[Dict[str, Any]]) -> str:
        """
        Takes raw census records and generates a natural language summary.
        """
        # Convert data to a concise string for the LLM
        data_str = "\n".join([
            f"Parish: {r['parish_id']}, Year: {r['year']}, "
            f"Parishioners: {r['total_parishioners']}, Baptisms: {r['baptisms']}"
            for r in data
        ])

        prompt = f"""
        You are a Data Analyst for the Catholic Diocese in Ghana. 
        Analyze the following census data and provide a concise 3-sentence summary 
        highlighting trends or significant observations:

        {data_str}

        Focus on total growth and baptism rates.
        """

        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content']
        except Exception as e:
            return f"AI Analysis currently unavailable: {str(e)}"

ai_service = AIService()
