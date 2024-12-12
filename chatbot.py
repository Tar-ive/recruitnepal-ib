import streamlit as st
from typing import Dict, List, Optional, Set
from utils import get_section_questions, generate_report, get_completion
from config import Parameters

class InterviewBot:
    """RecruitNepal's AI Interview Bot with structured interview flow."""

    def __init__(self):
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize session state variables."""
        if "candidate_name" not in st.session_state:
            st.session_state.candidate_name: Optional[str] = None
        if "current_section" not in st.session_state:
            st.session_state.current_section: Optional[str] = None
        if "questions" not in st.session_state:
            st.session_state.questions: Dict[str, List[str]] = {}
        if "answers" not in st.session_state:
            st.session_state.answers: Dict[str, List[str]] = {}
        if "question_index" not in st.session_state:
            st.session_state.question_index: int = 0
        if "evaluation" not in st.session_state:
            st.session_state.evaluation: Optional[str] = None
        if "report_path" not in st.session_state:
            st.session_state.report_path: Optional[str] = None
        if "total_questions_asked" not in st.session_state:
            st.session_state.total_questions_asked: int = 0
        if "asked_questions" not in st.session_state:
            st.session_state.asked_questions: Set[str] = set()

    def get_candidate_name(self) -> None:
        """Get the candidate's name."""
        with st.chat_message("assistant"):
            st.write(Parameters.INITIAL_GREETING)
        
        name = st.chat_input("Please enter your name...")
        if name:
            st.session_state.candidate_name = name
            st.rerun()

    def prepare_section_questions(self, section: str) -> None:
        """Prepare questions for a specific section."""
        if section not in st.session_state.questions:
            questions = get_section_questions(section)
            # Filter out any questions that have already been asked
            filtered_questions = [q for q in questions if q not in st.session_state.asked_questions]
            st.session_state.questions[section] = filtered_questions[:Parameters.QUESTIONS_PER_SECTION]
            st.session_state.answers[section] = []

    def should_continue_interview(self) -> bool:
        """Check if we should continue asking questions."""
        return st.session_state.total_questions_asked < Parameters.MAX_QUESTIONS

    def display_progress(self) -> None:
        """Display interview progress."""
        total = Parameters.MAX_QUESTIONS
        current = st.session_state.total_questions_asked
        st.progress(current / total, f"Question {current} of {total}")

    def display_chat_history(self) -> None:
        """Display previous questions and answers."""
        for section in Parameters.SECTIONS:
            if section in st.session_state.questions:
                questions = st.session_state.questions[section]
                answers = st.session_state.answers.get(section, [])
                
                for q, a in zip(questions, answers):
                    with st.chat_message("assistant"):
                        st.write(q)
                    with st.chat_message("user"):
                        st.write(a)

    def get_current_answer(self) -> None:
        """Get and process the current answer."""
        if not self.should_continue_interview():
            return

        section = st.session_state.current_section
        questions = st.session_state.questions[section]
        current_question = questions[st.session_state.question_index]

        if current_question not in st.session_state.asked_questions:
            answer = st.chat_input("Type your answer here...")
            if answer:
                st.session_state.answers[section].append(answer)
                st.session_state.asked_questions.add(current_question)
                st.session_state.total_questions_asked += 1
                st.session_state.question_index += 1
                
                # Move to next section if current section is complete
                if st.session_state.question_index >= len(questions):
                    st.session_state.question_index = 0
                    sections = list(Parameters.SECTIONS.keys())
                    current_index = sections.index(section)
                    
                    if current_index < len(sections) - 1 and self.should_continue_interview():
                        st.session_state.current_section = sections[current_index + 1]
                    else:
                        st.session_state.current_section = None
                
                st.rerun()

    def evaluate_interview(self) -> str:
        """Generate evaluation of all responses."""
        interview_text = ""
        for section, questions in st.session_state.questions.items():
            interview_text += f"\n{Parameters.SECTIONS[section]}:\n"
            answers = st.session_state.answers[section]
            for q, a in zip(questions, answers):
                interview_text += f"Q: {q}\nA: {a}\n"

        evaluation = get_completion(
            Parameters.EVALUATION_PROMPT.format(
                name=st.session_state.candidate_name,
                interview_text=interview_text
            )
        )

        interview_data = {
            'questions': st.session_state.questions,
            'answers': st.session_state.answers
        }
        report_path = generate_report(
            st.session_state.candidate_name,
            interview_data,
            evaluation
        )
        st.session_state.report_path = report_path
        
        return evaluation

    def execute_interview(self) -> None:
        """Main interview execution flow."""
        if not st.session_state.candidate_name:
            self.get_candidate_name()
            return

        # Start first section if no current section
        if st.session_state.current_section is None and not st.session_state.evaluation:
            if self.should_continue_interview():
                st.session_state.current_section = list(Parameters.SECTIONS.keys())[0]
            else:
                st.session_state.evaluation = self.evaluate_interview()

        # Display welcome message for new candidates
        if not any(st.session_state.questions):
            with st.chat_message("assistant"):
                st.write(f"Thank you, {st.session_state.candidate_name}! Let's begin the interview.")

        # Display progress
        self.display_progress()

        # Handle interview sections
        if st.session_state.current_section and self.should_continue_interview():
            self.prepare_section_questions(st.session_state.current_section)
            self.display_chat_history()
            
            with st.chat_message("assistant"):
                current_q = st.session_state.questions[st.session_state.current_section][st.session_state.question_index]
                st.write(current_q)
            
            self.get_current_answer()
        
        # Handle interview completion
        elif not st.session_state.evaluation:
            with st.spinner("Evaluating your responses..."):
                st.session_state.evaluation = self.evaluate_interview()
            
            st.success("Interview Complete!")
            st.info("AI Evaluation:")
            st.write(st.session_state.evaluation)
            
            if st.session_state.report_path:
                st.success(f"Interview report saved to: {st.session_state.report_path}")

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="RecruitNepal AI Interview Bot",
        page_icon="🤖",
        layout="centered"
    )

    st.title("🤖 RecruitNepal AI Interview Bot")
    st.markdown("""
    Welcome to RecruitNepal's AI-powered interview platform. We're here to help evaluate 
    your qualifications and match you with the perfect opportunity.
    """)

    bot = InterviewBot()
    bot.execute_interview()

    if st.session_state.evaluation:
        if st.button("Start New Interview", type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()