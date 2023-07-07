from flask import Flask, request, jsonify
import requests

app = Flask(__name__)



from bard import Bard
timeout = 30  # Increased timeout in seconds

@app.route('/api/ai', methods=['POST'])
def handle_post():
    data = request.get_json()

    
    if data:
        rules = data.get('rules', '.')
        
        bard = Bard(token="YAjim5M18K27kXedkuWI_6phq1LXgU-1u3gfLDbpgfubpIhn1AhN-OYdWhmNaRIwnTAChg.")
        res = bard.get_answer('Question:>>>>>'+data['question']+"<<<<<. Rules:>>>>> "+rules+'<<<<<')
        print(res)

        answer = res['content']
        links = res['links'][:10]
        images = list(res['images'])[:10]

        response_data = {
            'answer': answer,
            'links': links,
            'images': images
        }

        return jsonify(response_data)

    return jsonify({'error': 'No external data available'})

if __name__ == '__main__':
    app.run(debug=True)
