PUBLISHED = True
APP_URL = "https://lo-generator.streamlit.app"
APP_IMAGE = "lo_builder_flat.webp"

APP_TITLE = "Learning Objectives Builder"
APP_INTRO = """This micro-app allows you to generate learning objectives or validate alignment for existing learning objectives. It is meant as an experiment to explore how adoption, efficiency, and shareability of generative AI is affected when you wrap lightweight, hyper-personalized wrappers around it. Wrappers like this can take a few hours to build, which fast enough to justify building different micro-apps for different use cases. They also ideally codify good practices (in this case, instructional design practices) into AI prompting. 
"""

APP_HOW_IT_WORKS = """
 1. Fill in the details of the assessment.
2. Choose the language model.
3. Configure the prompt and additional options.
4. Generate Learning Objectives.
 """

SYSTEM_PROMPT = """System Prompt: You provide learning objectives that are specific, measurable, easy to understand, and suitable for an online course."""

PHASES = {
    "about": {
        "name": "Generate Learning Objectives",
        "fields": {
        	"request_type": {
                "type": "radio",
                "label": "What would you like to do?",
                "options": ["Provide learning objectives based on the content","Suggest learning objectives based on the title","Validate alignment between learning content and objectives"],
            },
            "title": {
                "type": "text_input",
                "label": """Enter the title for your course or module (optional)""",
                "value": "Introduction to Consumer Behavior",
            },
            "learning_content": {
                "type": "text_area",
                "height": 200,
                "label": "Enter your learning content",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Validate alignment between learning content and objectives"]}
            },
            "learning_objectives": {
                "type": "text_area",
                "label": "Enter your learning objectives:",
                "showIf": {"request_type": ["Validate alignment between learning content and objectives"]},
                "max_chars": 1000,
            },
            "lo_quantity": {
                "type": "slider",
                "label": "How many Learning Objectives would you like to generate?",
                "value": 4,
                "min_value": 1,
                "max_value": 8,
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "preferences": {
                "type": "markdown",
                "body": """<h3>Preferences (Beta Feature):</h3>""",
                "unsafe_allow_html": True,
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "learning_preferences": {
                "type": "checkbox",
                "label": "Engage a variety of learning preferences (e.g. Visual, Auditory, Kinesthetic)",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "relevance": {
                "type": "checkbox",
                "label": "Prioritize objectives that have real-world relevance",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "dash": {
                "type": "markdown",
                "body": """</hr>""",
                "unsafe_allow_html": True,
            },
            "preferences_2": {
                "type": "markdown",
                "body": """<h3>Bloom's Taxonomy</h3><p>Focus on these specific cognition goals:</p>""",
                "unsafe_allow_html": True,
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "goal_remember": {
                "type": "checkbox",
                "label": "Remember",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "goal_apply": {
                "type": "checkbox",
                "label": "Apply",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "goal_evaluate": {
                "type": "checkbox",
                "label": "Evaluate",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "goal_understand": {
                "type": "checkbox",
                "label": "Understand",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "goal_analyze": {
                "type": "checkbox",
                "label": "Analyze",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "goal_create": {
                "type": "checkbox",
                "label": "Create",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },

        },
        "phase_instructions": "The user will summarize the shared case study. Please critically review their response for accuracy. You will give them credit for mentioning Ebola, and you will be very pleased if they mention it is about Ebola with any other relevant details.",
        "user_prompt": [
            {
            	"condition": {"request_type": "Validate alignment between learning content and objectives"},
            	"prompt": """Please validate the alignment between the provided learning content and the learning objectives provided.\n
            			Be extremely strict and make sure that A) specific content exists that can be assessed to meet the learning objective and B) the learning objective is reasonable for an online course.)"""
            },
            {
            	"condition": {"request_type": "Suggest learning objectives based on the title"},
            	"prompt": "Please suggest {lo_quantity} learning objectives for the provided course. \n"
            },
			{
            	"condition": {"request_type": "Provide learning objectives based on the content"},
            	"prompt": "Please write {lo_quantity} learning objectives based on the provided content.\n"
            },
            {
                "condition": {"learning_objectives": True},
                "prompt": "Here are my learning objectives: {learning_objectives}"
            },
            {
                "condition": {},
                "prompt": "Provide learning objectives that are specific, measurable, easy to understand, and suitable for an online course.\nStart each learning objective with a verb from Bloom's taxonomy. **Avoid** verbs like \"understand\", \"learn\", or \"know\".",
            },
            {
                "condition": {},
                "prompt": """If I provide them, please focus on the following Bloom's Taxonomy verbs: 
                [Verbs List: 
                """
            },
            {
                "condition": {"goal_remember": True},
                "prompt": "Remember"
            },
            {
                "condition": {"goal_apply": True},
                "prompt": "Apply"
            },
            {
                "condition": {"goal_evaluate": True},
                "prompt": "Evaluate"
            },
            {
                "condition": {"goal_understand": True},
                "prompt": "Understand"
            },
            {
                "condition": {"goal_analyze": True},
                "prompt": "Analyze"
            },
            {
                "condition": {"goal_create": True},
                "prompt": "Create"
            },
            {
                "condition": {},
                "prompt": "]"
            },
			{
                "condition": {"learning_preferences": True},
                "prompt": "Try to engage a variety of learning modalities (e.g. Visual, Auditory, Kinesthetic) \n"
            },
            {
                "condition": {"relevance": True},
                "prompt": "Try to provide learning objectives that are relevant in the real world.\n"
            },
            {
            	"condition": {"request_type": "Provide learning objectives based on the content"},
            	"prompt": """Here is the content:
            	{learning_content}
            	"""
            },
            {
            	"condition": {"request_type": "Suggest learning objectives based on the title"},
            	"prompt": """Here is the title of my course:
            	{title}
            	"""
            },

            ],
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }

}

# def prompt_conditionals(prompt, user_input, phase_name=None):
#     #TO-DO: This is a hacky way to make prompts conditional that requires the user to know a lot of python and get the phase and field names exactly right. Future task to improve it. 

#     if user_input["request_type"] == "Validate alignment between learning content and objectives":
#         prompt = (
#             "Please validate the alignment between the provided learning content and the learning objectives provided.\n"
#             + "Be extremely strict and make sure that A) specific content exists that can be assessed to meet the learning objective and B) the learning objective is reasonable for an online course.")
#         if user_input["learning_objectives"]:
#             prompt += (
#             "Here are my learning objectives: \n"
#             + user_input["learning_objectives"] + "\n"
#             )
#         if user_input["learning_content"]:
#             prompt += (
#             "Here is the content: \n"
#             + "===============\n"
#             + user_input["learning_content"] + "\n"
#             )
#     else:
#         if user_input["request_type"] == "Suggest learning objectives based on the title":
#             prompt = "Please suggest " + str(user_input["lo_quantity"]) + " learning objectives for the provided course. \n"    
#             if any([user_input["goal_remember"], user_input["goal_apply"], user_input["goal_evaluate"], user_input["goal_understand"], user_input["goal_analyze"], user_input["goal_create"]]):
#                 prompt += "Focus specifically on these cognitive goals: " + user_input["goal_remember"] + "\n"
#                 if user_input["goal_remember"]:
#                     prompt+= "Remember \n"
#                 if user_input["goal_apply"]:
#                     prompt+= "Apply \n"
#                 if user_input["goal_evaluate"]:
#                     prompt+= "Evaluate \n"
#                 if user_input["goal_understand"]:
#                     prompt+= "Understand \n"
#                 if user_input["goal_analyze"]:
#                     prompt+= "Analyze \n"
#                 if user_input["goal_create"]:
#                     prompt+= "Create \n"
#                 prompt += ". \n"
#         else:
#             prompt = "Please write " + str(user_input["lo_quantity"]) + " learning objectives based on the provided content. \n"
#             if any([user_input["goal_remember"], user_input["goal_apply"], user_input["goal_evaluate"], user_input["goal_understand"], user_input["goal_analyze"], user_input["goal_create"]]):
#                 prompt += "Focus specifically on these cognitive goals: \n"
#                 if user_input["goal_remember"]:
#                     prompt+= "Remember \n"
#                 if user_input["goal_apply"]:
#                     prompt+= "Apply \n"
#                 if user_input["goal_evaluate"]:
#                     prompt+= "Evaluate \n"
#                 if user_input["goal_understand"]:
#                     prompt+= "Understand \n"
#                 if user_input["goal_analyze"]:
#                     prompt+= "Analyze \n"
#                 if user_input["goal_create"]:
#                     prompt+= "Create \n"
#                 prompt += ". \n"

#         prompt += "Provide learning objectives that are specific, measurable, easy to understand, and suitable for an online course. \n"
#         prompt += "Start each learning objective with a verb from Bloom's taxonomy. **Avoid** verbs like \"understand\", \"learn\", or \"know\".\n"
#         if user_input["learning_preferences"]:
#             prompt += "Try to engage a variety of learning modalities (e.g. Visual, Auditory, Kinesthetic) \n"
#         if user_input["relevance"]:
#             prompt += "Try to provide learning objectives that are relevant in the real world. \n"
#         if user_input["title"]:
#             prompt += "Here is the title of the course: " + user_input["title"] + "\n"
#         if user_input["learning_content"]:
#             prompt += (
#             "Here is the content: \n"
#             + "===============\n"
#             + user_input["learning_content"]
#             )


#     return prompt
    
PREFERRED_LLM = "gpt-4o-mini"
LLM_CONFIG_OVERRIDE = {}

SCORING_DEBUG_MODE = True
DISPLAY_COST = True

COMPLETION_MESSAGE = "You've reached the end! I hope you learned something!"
COMPLETION_CELEBRATION = False

RAG_IMPLEMENTATION = False # make true only when document exists
SOURCE_DOCUMENT = "sample.pdf" # file uploaded in source_docs if only

PAGE_CONFIG = {
    "page_title": "LO Generator",
    "page_icon": "️🔹",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())