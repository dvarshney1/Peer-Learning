# app.py


from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT
app = Flask(__name__)
app.config['DEBUG'] = True


@app.route('/run_code', methods=['POST'])
def run_code():
    """Run python 3 code
        :return: JSON object of python 3 output
            {
                ...
            }
    """

    output = None
    code = request.json['code']

    cmd = 'python -c "' + code +'"'
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE,
              stderr=STDOUT, close_fds=True)
    output = p.stdout.read()

    return jsonify(output.decode('utf-8'))


if __name__ == "__main__":
    app.run(debug=True)
