from flask import Flask, render_template, jsonify

from flask_bootstrap import Bootstrap

from arduino_publisher.arduino_reader import ArduinoReader

app = Flask(__name__)
app.secret_key = 'adefasdfv'

app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'

bootstrap = Bootstrap(app)
reader = ArduinoReader()


@app.route('/')
def index():
    return render_template('values_monitor.html')

@app.route('/serial_monitor')
def serial_monitor():
    return render_template('serial_monitor.html')

@app.route('/serial_monitor_data')
def serial_monitor_data():
    return jsonify(reader.get_serial_monitor())

@app.route('/metrics')
def prometheus_metrics():
    return reader.get_prometheus_metrics()

@app.route('/parsed_values_data')
def parsed_values_data():
    return jsonify(reader.get_parsed_values())


if __name__ == '__main__':
    reader.start()
    app.run(host="0.0.0.0", debug=True, use_reloader=False)
