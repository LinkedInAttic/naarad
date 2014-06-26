from os import listdir
from flask import Flask, jsonify, render_template, request

import anomly

app = Flask(__name__)

@app.route('/_get_anomaly')
def try_anom():
	
	metric_name = request.args.get('metric')
	bitmapdtc = anomly.BitmapDetector('static/orig/'+metric_name)
	deridtc = anomly.DetrivativeDetector('static/orig/'+metric_name)
	emadtc = anomly.expAvgDetector('static/orig/'+metric_name)
	
	bitmapdtc_rst = bitmapdtc.generate_anom_data('bitmap'+metric_name)
	deridtc_rst = deridtc.generate_anom_data('deri'+metric_name)
	emadtc_rst = emadtc.generate_anom_data('ema'+metric_name)

	rsts = {
			'bitmap': bitmapdtc_rst,
			'deri': deridtc_rst, 
			'ema': emadtc_rst
	}

	return jsonify(result = rsts)

@app.route('/load_metrics_select')
def load_metrics_select():
	return jsonify(result = listdir('static/orig'))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')