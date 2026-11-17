import streamlit as st
from helpers.gemini_utils import get_gemini_model, extract_gemini_text, configure_gemini

def ROADMAP():
    configure_gemini()
    st.title("Daily Course Planner")

    with st.form("user_input"):
        name = st.text_input("Please tell us your name")

        col1, col2 = st.columns(2)
        with col1:
            course = st.text_input("Which course do you want to learn")
        with col2:
            learning_level = st.selectbox("Choose your level of learning",
                                          ["Beginner", "Intermediate", "Advanced"])

        col3, col4 = st.columns(2)
        with col3:
            no_of_hours = st.number_input("Choose number of learning hours per day",
                                          value=1, min_value=1, max_value=24)
        with col4:
            no_of_days = st.number_input("How many days you want to learn the skill",
                                         value=1, min_value=1, max_value=365)

        target_level = st.selectbox(
            "To which level do you want to reach at the end of the preparation",
            ["Intermediate", "Advanced"])

        submit = st.form_submit_button("Submit")

    if submit:
        if not course:
            st.error("Please enter a course name.")
            return

        with st.spinner(text="Generating your customized learning roadmap..."):
            prompt_template = f'''You are a course instructor for {course}.
I am your student with a {learning_level} background.
I want to learn {course} in {no_of_days} days by spending {no_of_hours} hours daily.
At the end of preparation I need to reach {target_level}.
Generate a comprehensive, structured daily study plan to reach {target_level}.
Include:
- A motivational quote at the beginning.
- Daily schedule breakdown (e.g., DAY 1, DAY 2...).
- Recommended topics, practice exercises, and daily revision time blocks.
- Format with clear Markdown headings, lists, and time blocks.
'''
            try:
                model = get_gemini_model()
                response = model.generate_content(prompt_template)
                plan = extract_gemini_text(response)
                if plan:
                    st.markdown(plan)
                    st.download_button(
                        label="Download plan as text",
                        data=plan,
                        file_name=f"{course}_{no_of_days}_day_plan.txt",
                        mime="text/plain",
                    )
                else:
                    st.error("Could not generate plan. Please try again.")
            except Exception as e:
                st.error(f"Error generating roadmap: {e}")
