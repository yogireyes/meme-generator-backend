## Meme-Generator - Backend

#### Live at: https://muhammadabir64-meme-generator.netlify.app
#### Frontend repository: https://github.com/muhammadabir64/meme-generator-frontend

* Requirements:
  - Python v3.12

## how to setup?
1. Clone Repository:
```
https://github.com/muhammadabir64/meme-generator-backend
```
2. Install Dependencies:
```
pip install -r requirements.txt
```
3. Set ElephantSQL URL in `.env`:
```
SQLALCHEMY_DATABASE_URI=postgresql://
```
4. Migrate Database
```
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```
5. Start the server:
```
python app.py
```