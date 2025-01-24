from flask import Flask, render_template, request, jsonify, send_file, make_response
import os
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from openai import OpenAI
from dotenv import load_dotenv
import time
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        if not file:
            app.logger.error("No file uploaded")
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        app.logger.info(f"File uploaded: {file_path}")

        # Ensure file is accessible
        with open(file_path, 'rb') as f:
            app.logger.info(f"Reopened file for reading: {file_path}")

        # Extract text based on file type
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            text = extract_text_from_image(file_path)
        elif filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        else:
            os.remove(file_path)
            app.logger.error("Unsupported file type")
            return jsonify({"error": "Unsupported file type"}), 400

        os.remove(file_path)
        app.logger.info(f"Text extracted: {text[:100]}...")

        # Extract and solve problems
        problems = extract_physics_problems(text)
        app.logger.info(f"Problems extracted: {problems}")

        solutions = solve_physics_problems(problems)
        app.logger.info(f"Solutions provided in LaTeX: {solutions}")

        # Return problems and LaTeX solutions
        return jsonify({"problems": problems, "solutions": solutions})

    except MemoryError as me:
        app.logger.error(f"Memory error: {me}")
        return jsonify({"error": "Server out of memory"}), 500

    except Exception as e:
        app.logger.error(f"Error processing file: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/download-solutions-pdf', methods=['POST'])
def download_solutions_pdf():
    try:
        solutions = request.json.get('solutions', [])
        if not solutions:
            raise ValueError("No solutions provided")

        # Generate PDF content
        pdf_content = generate_pdf_content(solutions)

        # Create a BytesIO buffer to hold the PDF data
        pdf_buffer = io.BytesIO()
        pdf_buffer.write(pdf_content)
        pdf_buffer.seek(0)

        # Create a response with the PDF data
        response = make_response(send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='solutions.pdf'))
        response.headers['Content-Disposition'] = 'attachment; filename=solutions.pdf'
        return response
    except Exception as e:
        app.logger.error(f"Error generating PDF: {e}")
        return "Internal Server Error", 500

def generate_pdf_content(solutions):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Solutions:", styles['Title']))

    for solution in solutions:
        # Assuming solutions are in LaTeX, render them properly using Matplotlib or similar tool
        formatted_solution = f"$$ {solution} $$"  # This is a placeholder for LaTeX rendering
        elements.append(Paragraph(formatted_solution, styles['BodyText']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

def extract_text_from_image(image_path):
    """Extract text from an image using Tesseract OCR."""
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF using PyMuPDF."""
    text = ""
    pdf_document = fitz.open(pdf_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text += page.get_text()
    return text

def extract_physics_problems(text):
    """Use GPT to identify and extract questions from the text."""
    prompt = f"""
    The following text contains a physics assignment. Extract each individual question clearly and concisely:

    {text}

    List the questions one by one.
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that processes text to extract questions."},
            {"role": "user", "content": prompt}
        ]
    )
    questions = response.choices[0].message.content.strip().split("\n")
    return [q.strip() for q in questions if q.strip()]

def solve_physics_problems(problems):
    """Use GPT to solve physics problems and provide step-by-step solutions in LaTeX."""
    solutions = []
    for problem in problems:
        prompt = f"""
        Solve the following physics problem and provide a detailed solution in LaTeX format. 
        The solution should include the necessary formulas, steps, and final answer, all written clearly in LaTeX.

        Problem:
        {problem}

        Ensure that the solution is concise and avoids generating multiple variations.
        """
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a physics expert providing detailed solutions in LaTeX format."},
                {"role": "user", "content": prompt}
            ]
        )
        solution = response.choices[0].message.content.strip()
        solutions.append(solution)
    return solutions

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
