import os
import streamlit as st
from helpers.toast_messages import get_random_toast
from helpers.quiz import get_quiz_data
from helpers.quiz_utils import string_to_list, get_randomized_options
from helpers.gemini_utils import get_gemini_model, extract_gemini_text, configure_gemini

def TEST(username=''):
    configure_gemini()
    st.title("Start taking Skill Test from the skills you have learnt")

    # Check if user is new or returning using session state.
    if 'first_time' not in st.session_state:
        message, icon = get_random_toast()
        st.toast(message, icon=icon)
        st.session_state.first_time = False

    st.title(":red[QuizBuddy] — Learn.Quiz.Practice  🧠", anchor=False)

    with st.form("user_input"):
        cl1, cl2 = st.columns(2)
        with cl1:
            skill = st.text_input("Enter the skill that you want to take the test")
        cl3, cl4 = st.columns(2)
        with cl3:
            skill_level = st.selectbox("At which level are you in the skill", ["Beginner", "Intermediate", "Advanced"])
        with cl2:
            skill_topic = st.text_input("On what topic in skill you want to take on?")
        with cl4:
            number_of_questions = st.number_input("Choose number of questions", value=1, min_value=1, max_value=10)
        number_of_questions = str(number_of_questions)
        submitted = st.form_submit_button("Craft my quiz!")

    if submitted or ('quiz_data_list' in st.session_state):
        with st.spinner("Crafting your quiz...🤓"):
            if submitted:
                quiz_data_str = get_quiz_data(skill=skill, level=skill_level, topic=skill_topic, number_of_questions=number_of_questions)
                st.session_state.quiz_data_list = string_to_list(quiz_data_str)

                # Reset answers and options for the new quiz
                st.session_state.user_answers = [None for _ in st.session_state.quiz_data_list]
                st.session_state.correct_answers = []
                st.session_state.randomized_options = []

                for q in st.session_state.quiz_data_list:
                    options, correct_answer = get_randomized_options(q[1:])
                    st.session_state.randomized_options.append(options)
                    st.session_state.correct_answers.append(correct_answer)

            with st.form(key='quiz_form'):
                st.subheader("🧠 Quiz Time: Test Your Knowledge!", anchor=False)
                for i, q in enumerate(st.session_state.quiz_data_list):
                    options = st.session_state.randomized_options[i]
                    default_index = st.session_state.user_answers[i] if st.session_state.user_answers[i] is not None else 0
                    response = st.radio(q[0], options, index=default_index, key=f"q_{i}")
                    user_choice_index = options.index(response)
                    st.session_state.user_answers[i] = user_choice_index

                results_submitted = st.form_submit_button(label='Unveil My Score!')

                if results_submitted:
                    score = sum([ua == st.session_state.randomized_options[i].index(ca) for i, (ua, ca) in
                                 enumerate(zip(st.session_state.user_answers, st.session_state.correct_answers))])
                    st.success(f"Your score: {score}/{len(st.session_state.quiz_data_list)}")

                    if score == len(st.session_state.quiz_data_list):
                        st.balloons()
                    else:
                        incorrect_count = len(st.session_state.quiz_data_list) - score
                        if incorrect_count == 1:
                            st.warning("Almost perfect! You got 1 question wrong. Let's review it:")
                        else:
                            st.warning(f"Almost there! You got {incorrect_count} questions wrong. Let's review them:")

                    for i, (ua, ca, q, ro) in enumerate(
                            zip(st.session_state.user_answers, st.session_state.correct_answers,
                                st.session_state.quiz_data_list, st.session_state.randomized_options)):
                        with st.expander(f"Question {i + 1}", expanded=False):
                            if ro[ua] != ca:
                                st.info(f"Question: {q[0]}")
                                st.error(f"Your answer: {ro[ua]}")
                                st.success(f"Correct answer: {ca}")

                                quiz_data = " ".join(map(str, st.session_state.quiz_data_list))
                                prompt_template = f"""This is a quiz question on {skill} ({skill_topic}) at {skill_level} level.
Question: {q[0]}
User chose: {ro[ua]}
Correct answer: {ca}
Write a short, crisp explanation of why {ca} is the correct answer."""
                                model = get_gemini_model()
                                response = model.generate_content(prompt_template)
                                explanation = extract_gemini_text(response)
                                if explanation:
                                    st.info(explanation)
