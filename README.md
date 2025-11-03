# Real-Time Digital Signage System

> **Abstract** : This project aims to develop a Real-Time Digital Signage System that enables users to upload and display images, text, or videos on a TV screen instantly. The system provides a user-friendly interface for managing content, ensuring seamless updates without manual intervention. Designed for applications such as advertisements, announcements, and information displays, this system is ideal for malls, offices, educational institutions, and public spaces. The TV screen automatically updates whenever new content is added, making it a dynamic and efficient solution for real-time content management.
> <br><br> 
> The Digital Signage System is a real-time, two-page signage solution developed primarily using HTML, CSS, and Vanilla JavaScript, with supporting Python components. Designed for dynamic public information display, the system enables administrators to update and broadcast content instantly across screens. Its modular architecture allows seamless integration of multimedia and interactive elements, ensuring a visually engaging and responsive user experience. The project emphasizes simplicity and reliability, making it suitable for a wide range of environments such as retail, education, and transportation hubs. By leveraging web technologies, the signage system achieves cross-platform compatibility and ease of deployment, supporting efficient communication and timely updates.

## Features include 
- Supports text, image (png, jpg, etc) and video (mp4, mov, etc) inputs.

### Text Based Features
1. Quill.js-based editor for text formatting (colors, bold, italic, underline, alignments).
2. Scroll feature which scrolls the text input across the Display Screen in an endless loop.

### Image/Video Based Features
1. Single image/video input will be on display until Display Screen is cleared or new input is given.
2. Videos will autoplay with sound. (Read Note...)
3. Video controls (Play, Pause, Mute, Unmute) will be displayed when a single video input is sent.
4. Supports multi file inputs, where images would be displayed in an endless looping slideshow of 5 seconds, while the entire video plays.
5. Drag and Drop feature.

<b>Note: Autoplay with Sound Blocked</b>
<br> 
Modern browsers prevent videos from automatically playing with sound until you've interacted with a page (such as clicking anywhere on the Display Page). To enable video playback with sound, please interact with the Display Page at least once.

## Project Members
1. CHOUDHRY ABDUL REHMAN MOHD ASIM  [ Team Leader ] 
2. SADRIWALA MOHAMMED FIROZ 
3. PATHAN MUGAIRA ZAKEER 
4. SHAIKH ADYAN ATAULLAH 

## Project Guides
1. PROF. MOHD ASHFAQUE SHAIKH  [ Primary Guide ] 

## Deployment Steps
Please follow the below steps to run this project.
<br>
Step 1: Open terminal and run the following command: 
```bash
pip install -r requirements.txt 
```
Step 2: Run the server (app.py).
<br>
Step 3: 'ctrl + click' on http://127.0.0.1:5000.
<br>
Step 3: The main link is the Login page which redirects to the Editor page.
<br>
Step 4: The main link is also used to open the Display page by inputting "/other" at the end of the link, or by replacing "/editor" with "/other" if logged in to the Editor page.
<br>
Step 5: Setup the Display page on a broadcasting display device and the Editor page on your laptop (preferred) or phone.
<br><br>
<b>Note:</b> The Login credentials are hardcoded, with the Username as "RizviSignage" and the Password as "CodeLike".

## Subject Details
- Class : SE (COMP) Div A - 2024-2025
- Subject : Mini Project 1-B (MP-1(P)(2019))
- Project Type : Mini Project

## Platform, Libraries and Frameworks used
1. [VSCode](https://code.visualstudio.com/)
2. [Flask](https://flask.palletsprojects.com/en/stable/)
3. [Flask-Socketio](https://flask-socketio.readthedocs.io/en/latest/)
4. [Werkzeug](https://werkzeug.palletsprojects.com/en/stable/)
5. [JavaScript (Vanilla)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
6. [JS Socketio](https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js)
7. [Quill.js](https://cdn.quilljs.com/1.3.6/quill.js)

## References
- [https://github.com/](https://github.com/)
- [https://flask-socketio.readthedocs.io/en/latest/](https://flask-socketio.readthedocs.io/en/latest/)
