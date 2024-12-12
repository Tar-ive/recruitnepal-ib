from typing import List, Dict
import re
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from config import Parameters

class OpenAIClient:
    """A wrapper class for OpenAI API operations."""
    
    def __init__(self):
        self.client = OpenAI()
    
    def get_completion(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=Parameters.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"Error in OpenAI API call: {str(e)}")
            raise

def get_section_questions(section: str) -> List[str]:
    """Get questions for a specific interview section."""
    prompt = Parameters.QUESTIONS_PROMPT.format(section=section)
    raw_questions = ai_client.get_completion(prompt)
    
    # Extract numbered questions
    questions = []
    for line in raw_questions.split('\n'):
        if line.strip() and any(line.startswith(str(i)) for i in range(1, 4)):
            question = re.sub(r'^\d+\.\s*', '', line.strip())
            questions.append(question)
    
    return questions[:Parameters.QUESTIONS_PER_SECTION]

def generate_report(name: str, interview_data: Dict, evaluation: str) -> str:
    """Generate and save a markdown report for the candidate."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format interview text
    interview_text = ""
    for section, questions in interview_data['questions'].items():
        interview_text += f"\n### {Parameters.SECTIONS[section]}\n"
        for q, a in zip(questions, interview_data['answers'][section]):
            interview_text += f"\n**Q:** {q}\n**A:** {a}\n"
    
    # Extract recommendation from evaluation
    recommendation = evaluation.split("Overall Recommendation:")[-1].strip() if "Overall Recommendation:" in evaluation else ""
    
    # Generate report content
    report_content = Parameters.REPORT_TEMPLATE.format(
        timestamp=timestamp,
        name=name,
        date=datetime.now().strftime("%Y-%m-%d"),
        interview_text=interview_text,
        evaluation=evaluation,
        recommendation=recommendation
    )
    
    # Save report
    report_path = Parameters.REPORTS_DIR / f"{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
    report_path.write_text(report_content)
    
    return str(report_path)

# Create singleton instance
ai_client = OpenAIClient()

# Wrapper function
def get_completion(prompt: str) -> str:
    return ai_client.get_completion(prompt)