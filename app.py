import pathlib
import datetime
import json
import csv
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

SPARK_METADATA_PATH = pathlib.Path('/Users/gabriel/Documents/Unit/BigData/detector_fraude/results/_spark_metadata')
SPARK_STREAM_PATH = pathlib.Path('/Users/gabriel/Documents/Unit/BigData/detector_fraude/stream')
BATCH_PATH = pathlib.Path('batch.csv')
BATCH_FIELDNAMES = ['type', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']
STEP = 1

@app.route('/', methods=['GET', 'POST'])
def index():
    global STEP
    if request.method == 'GET':
        batch_rows = []
        if BATCH_PATH.exists():
            with open(BATCH_PATH, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    batch_rows.append(row)
        return render_template('index.html', batch_rows=batch_rows, table_headers=BATCH_FIELDNAMES, step=STEP)
    
    write_header = not BATCH_PATH.exists() or BATCH_PATH.stat().st_size == 0
    with open(BATCH_PATH, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=BATCH_FIELDNAMES)
        if write_header:
            writer.writeheader()
        row = {
            'type': int(request.form['type']),
            'amount': int(request.form['quantidade']),
            'oldbalanceOrg': int(request.form['saldoAnteriorOrigem']),
            'newbalanceOrig': int(request.form['novoSaldoOrigem']),
            'oldbalanceDest': int(request.form['saldoAnteriorDestino']),
            'newbalanceDest': int(request.form['novoSaldoDestino'])
        }
        writer.writerow(row)
    STEP += 1
    return redirect(url_for('index'))

@app.route('/result', methods=['GET'])
def result():
    csv_paths = []
    metadata_files = tuple(SPARK_METADATA_PATH.glob('*'))
    if len(metadata_files) == 0:
        return render_template('result.html', result_keys=[], results=[])
    for metadata_file in metadata_files:
        with open(metadata_file, 'r') as f:
            f.readline()
            csv_paths.append(pathlib.Path(json.load(f)['path'].replace('file://', '')))
    results = []
    fieldnames = BATCH_FIELDNAMES + ['prediction']
    for csv_path in csv_paths:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                results.append(row)
    return render_template('result.html', result_keys=fieldnames, results=results)

@app.route('/batch/enviar', methods=['POST'])
def enviar_batch():
    global STEP
    if BATCH_PATH.exists():
        BATCH_PATH.rename(SPARK_STREAM_PATH.joinpath(BATCH_PATH.stem + str(STEP-1) + '.csv'))
    return redirect(url_for('index'))
