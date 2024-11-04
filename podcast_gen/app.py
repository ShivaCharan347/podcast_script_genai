import os
import re
import pdfkit
from flask import Flask, render_template, request, redirect, url_for, make_response
from groq import Groq



# Instantiation of Groq Client
client = Groq(api_key=os.environ.get("GROQ_APIKEY"))

app = Flask(__name__)

# Function to generate podcast conversation
def generate_podcast_conversation(topic, podcaster_name, guest_name, language):
    app.logger.debug("Generating podcast conversation")
    app.logger.debug(f"Topic: {topic}, Podcaster: {podcaster_name}, Guest: {guest_name}, Language: {language}")

    if not topic:
        app.logger.warning("No topic provided")
        return "Please enter a topic."

    llm = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
                Generate a complete podcast conversation between Podcaster {podcaster_name} and Guest {guest_name} on the topic '{topic}' \
                in the language '{language}'. 
                The conversation should be fully written in {language} and contain at least 20-30 back-and-forth exchanges.
                """
            },
            {
                "role": "user",
                "content": f"Let's start a podcast about {topic}. The podcaster's name is {podcaster_name} and the guest's name is \
                    {guest_name}."
            }
        ],
        model="gemma2-9b-it",
    )
    
    app.logger.debug("Podcast conversation generated successfully")
    return llm.choices[0].message.content

@app.route('/')
def index():
    app.logger.debug("Rendering index page")
    return render_template('index.html')

@app.route('/services', methods=['GET', 'POST'])
def services():
    if request.method == 'POST':
        app.logger.debug("POST request received on /services")
        topic = request.form.get('topic')
        podcaster_name = request.form.get('podcaster_name', 'Podcaster')
        guest_name = request.form.get('guest_name', 'Guest')
        language = request.form.get('language', 'English')

        app.logger.debug(f"Form data - Topic: {topic}, Podcaster: {podcaster_name}, Guest: {guest_name}, Language: {language}")

        if not topic:
            app.logger.warning("No topic provided in form submission")
            return render_template('services.html', error="Please provide a podcast topic.")
        
        # Generate the podcast conversation
        podcast_script = generate_podcast_conversation(topic, podcaster_name, guest_name, language)

        # Replace **text** with <h4>text</h4> for bold text
        podcast_script = re.sub(r'\*\*(.*?)\*\*', r'<h5>\1</h5>', podcast_script)
        
        # Remove leading * from bullet points
        podcast_script = re.sub(r'^\*\s*', '', podcast_script, flags=re.MULTILINE)
        
        # Wrap the main headings
        podcast_script = re.sub(r'## (.*?)\n', r'<h5>\1</h5>\n', podcast_script)  # Convert 
        
        podcast_script = re.sub(r'# (.*?)\n', r'<h5>\1</h5>\n', podcast_script)   # Convert 

        # Render result page with the generated podcast script
        app.logger.debug("Rendering result page with podcast script")
        return render_template('result.html', podcast_script=podcast_script)
    
    app.logger.debug("GET request received on /services")
    return render_template('services.html')


@app.route('/result')
def result():
    # Assume `podcast_script` is generated or passed here
    app.logger.debug("GET request received on /result")
    return render_template('result.html', podcast_script=None)
# Specify the path to the wkhtmltopdf executable
# config = pdfkit.configuration(wkhtmltopdf=r'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')

@app.route('/download_pdf', methods=['GET'])

def download_pdf():
    podcast_script = request.args.get('podcast_script')
    rendered_html = render_template('pdf_template.html', podcast_script=podcast_script)

    # Generate PDF using the specified configuration
    pdf = pdfkit.from_string(rendered_html, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=podcast.pdf'
    return response


if __name__ == '__main__':
    app.run(debug=True)
