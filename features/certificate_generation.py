import cv2
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cert_path = os.path.join(BASE_DIR, "certificate", "certificate!.jpeg")
certificate_template = cv2.imread(cert_path)

# Function to generate the certificate
def generate_certificate(name):
    # Make a copy of the template
    certificate = certificate_template.copy()

    # Add the name to the certificate
    font = cv2.FONT_HERSHEY_TRIPLEX
    text_color = (0, 0, 0)  # Black color
    text_thickness = 5
    text_size, _ = cv2.getTextSize(name, font, 1, text_thickness)
    text_x = 600- text_size[0] // 2  # Center the text horizontally
    text_y = 600
    cv2.putText(certificate, name, (text_x, text_y), font, 3, text_color, text_thickness)

    # Encode the certificate as PNG
    _, encoded_certificate = cv2.imencode(".png", certificate)
    return encoded_certificate

if __name__=='__main__':
    generate_certificate("Praveen")