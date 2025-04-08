from flask import Flask, render_template, request, send_from_directory
import hashlib
import json
import os
import time
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Config
INSTITUTE_NAME = "Institute of Blockchain Studies"
PDF_FOLDER = "certificates"
QR_FOLDER = "qrcodes"
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# Blockchain structure
class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_certificate(self, data):
        latest_block = self.get_latest_block()
        new_block = Block(len(self.chain), time.time(), data, latest_block.hash)
        self.chain.append(new_block)
        return new_block

    def verify_certificate(self, cert_data, cert_hash):
        for block in self.chain:
            if block.data == cert_data and block.hash == cert_hash:
                return True
        return False

blockchain = Blockchain()

# QR and PDF Generation
def create_qr_code(data, filename):
    qr = qrcode.make(data)
    filepath = os.path.join(QR_FOLDER, filename)
    qr.save(filepath)
    return filepath

def generate_pdf_certificate(cert_data, hash):
    filename = f"{cert_data['name'].replace(' ', '_')}_cert.pdf"
    pdf_path = os.path.join(PDF_FOLDER, filename)
    qr_path = create_qr_code(hash, f"{cert_data['name']}_qr.png")

    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 750, INSTITUTE_NAME)

    c.setFont("Helvetica", 18)
    c.drawCentredString(300, 700, "Certificate of Completion")

    c.setFont("Helvetica", 14)
    c.drawString(100, 630, "This is to certify that:")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 610, cert_data['name'])

    c.setFont("Helvetica", 14)
    c.drawString(100, 590, "has successfully completed the course:")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 570, cert_data['course'])

    c.setFont("Helvetica", 14)
    c.drawString(100, 550, f"Date: {cert_data['date']}")

    c.setFont("Helvetica", 10)
    c.drawString(100, 520, f"Blockchain Certificate Hash: {hash}")

    c.drawImage(qr_path, 400, 500, width=100, height=100)

    c.save()
    return filename

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        name = request.form['name']
        course = request.form['course']
        date = request.form['date']

        cert_data = {
            "name": name,
            "course": course,
            "date": date
        }

        block = blockchain.add_certificate(cert_data)
        cert_hash = block.hash

        pdf_filename = generate_pdf_certificate(cert_data, cert_hash)

        return render_template('generated.html', hash=cert_hash, cert=cert_data, pdf=pdf_filename)
    return render_template('generate.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        name = request.form['name']
        course = request.form['course']
        date = request.form['date']
        cert_hash = request.form['hash']

        cert_data = {
            "name": name,
            "course": course,
            "date": date
        }

        valid = blockchain.verify_certificate(cert_data, cert_hash)
        return render_template('result.html', valid=valid)
    return render_template('verify.html')

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(PDF_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
