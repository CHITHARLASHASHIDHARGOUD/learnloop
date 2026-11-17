import os
import google.generativeai as genai
from features.apikeys import GEMINIAI_API_KEY
from helpers.gemini_utils import get_gemini_model, extract_gemini_text
from youtube_transcript_api import YouTubeTranscriptApi

def get_video_text(video_url):
    try:
        video_id = video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

        transcript = ""
        for i in transcript_text:
            transcript += " " + i['text']

        return transcript

    except Exception as e:
        raise e

def get_quiz_data(skill, level, topic, number_of_questions):
    prompt_template = f"""
    You are a helpful assistant programmed to generate multiple choice quiz questions based on the skill, level, and topic provided.
    Generate exactly {number_of_questions} questions.
    Each question must have 1 correct answer and 3 incorrect answers (total 4 options).
    Adhere strictly to this output format as a Python list of lists with NO extra commentary or variable assignment:
    [
        ["Question 1 text", "Correct Answer", "Incorrect Option 1", "Incorrect Option 2", "Incorrect Option 3"]
    ]
    Skill: {skill}
    Level: {level}
    Topic: {topic}
    Number of questions: {number_of_questions}
    """
    model = get_gemini_model()
    response = model.generate_content(prompt_template)
    return extract_gemini_text(response)
