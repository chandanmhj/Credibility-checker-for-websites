from flask import Flask, render_template, request, jsonify
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from credibility_checker import CredibilityChecker

app = Flask(__name__)
checker = CredibilityChecker()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_credibility():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Check website
        result = checker.check_website(url)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    '''Simple test endpoint'''
    result = checker.check_website('https://www.wikipedia.org')
    return jsonify(result)

if __name__ == '__main__':
    print('Starting Website Credibility Checker...')
    print('Open http://localhost:5000 in your browser')
    app.run(debug=True, port=5000)