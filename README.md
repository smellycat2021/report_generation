/REPORT
|-- app.py                  # Flask application & API endpoints
|-- config.py
|-- data_processor.py
|-- report_generator.py
|-- /uploads
|-- /reports
|
|-- /client                 # <-- Frontend files served here
|   |-- index.html          # The main page structure
|   |-- styles.css          # Styling for the UI
|   |
|   |-- /ts                 # <-- Directory for TypeScript source code
|   |   |-- **app.ts** # Main application logic (API calls, event handlers)
|   |   |-- **interfaces.ts** # Data type definitions (UploadResponse, ReportGenerationResponse)
|   |
|   |-- /dist               # <-- Compiled JavaScript output
|   |   |-- app.js          # The compiled/transpiled JavaScript file
|
|-- tsconfig.json           # TypeScript compiler configuration

bash
python3 -m venv venv
source venv/bin/activate
pip install Flask
flask run
pip install Pandas
pip install flask_sqlalchemy
npm install typescript --save-dev
npx tsc
npx tsc --watch
pip install openpyxl

export FLASK_ENV=development
pip install XlsxWriter

pip install gunicorn
gunicorn app:app -b 0.0.0.0:8000 // This command starts your app on port 8000, accessible to the public internet (usually proxied through the host's port 80/443).

pip freeze > requirements.txt

git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/smellycat2021/report_generation.git
git push -u origin main

# report_generation
