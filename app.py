import os
from os.path import join, dirname
from dotenv import load_dotenv
from flask import (Flask, request, render_template, redirect, url_for, jsonify, )
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)



@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template('index.html', words=words, msg=msg)

# Route detail
@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = 'cbcdb0fe-8a23-45dd-a772-4a505dc9fd05'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        suggestions = request.args.get('suggestions', '')  # Ambil saran kata dari argumen URL
        return redirect(url_for(
            'error',
            msg=f'could not find the word, "{keyword}", did you mean: {suggestions}'
        ))
    if type(definitions[0]) is str:
        suggestions = ','.join(definitions)
        return redirect(url_for(
            'error',
            msg=f'could not find the word, "{keyword}", did you mean: {suggestions}'
        ))
    status = request.args.get('status_give', 'new')
    return render_template('detail.html', word=keyword, definitions=definitions, status=status)

# Route untuk halaman error
@app.route('/error')
def error():
    msg = request.args.get('msg', 'An error occurred.')
    suggestions = request.args.get('suggestions', '').split(',')  # Ambil daftar saran kata dari argumen URL
    return render_template('error.html', msg=msg, suggestions=suggestions)

# Route untuk menyimpan kata
@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y%m%d'),
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

@app.route('/api/delete_word', methods=["POST"])
def delete_word():
    word=request.form.get('word_give')
    db.words.delete_one({"word":word})
    db.examples.delete_many({'word':word})
    return jsonify(
        {
            "result":"success",
            "msg":f"the word, {word} ,was deleted",
        }
    )
@app.route('/api/get_exs',methods=["GET"])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id')),  # Menggunakan "_id" yang benar
        })
    return jsonify({'result': 'success', 'examples': examples})  # Mengembalikan data contoh
@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word=request.form.get('word')
    example=request.form.get('example')
    doc={
        'word':word,
        'example':example,
    }
    db.examples.insert_one(doc)
    return jsonify ({
        'result':'success',
        "msg":f'example your ,{example}, for the word ,{word}'
    })
    return jsonify({'result': 'success'})


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id=request.form.get('id')
    word=request.form.get('word')
    db.examples.delete_one({'_id':ObjectId (id)})
    return jsonify({
        'result':  'success',
        'msg' :f'your exampp {word}, was deleted!',
        })
# Jalankan aplikasi jika file ini dijalankan sebagai program utama
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
