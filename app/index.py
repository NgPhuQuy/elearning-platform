from app import app

@app.route('/')
def index():
    pass

if __name__ == '__main__':
    app.run(debug=True)