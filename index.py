import math
import random
import yfinance as yf
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import boto3
import time
import os

os.environ['AWS_SHARED_CREDENTIALS_FILE'] = './cred'

app = Flask(__name__)
results = []
resources = []  # Placeholder for initialized resources
is_initialized = False
selected_service = None

# Create an S3 client
s3_client = boto3.client('s3')

@app.route('/')
def home():
    global is_initialized
    return render_template('init.html', is_initialized=is_initialized)

@app.route('/init', methods=['POST'])
def init():
    global resources, is_initialized, selected_service, start_time
    service = request.form.get('service')
    num_resources = int(request.form.get('resources', 0))


    selected_service = service
    is_initialized = True

    # Warm up the EC2 instances
    if service == 'ec2':
        start_time = time.time()
        resources = start_ec2_instances(service, num_resources)
    else:
        # For other services (e.g., Lambda), you can add the warm-up logic here if needed
        resources = []

    return render_template('home.html')

def start_ec2_instances(service, num_resources):
    ec2_resource = boto3.resource(service, region_name='us-east-1')  # Add the AWS region you're using here

    instances = []

    for i in range(num_resources):
        instance = ec2_resource.create_instances(
            ImageId='ami-0e84bfd96c6321007',  # Your AMI ID here
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro'  # Instance type (this is a free tier instance type)
        )[0]

        instances.append(instance.id)  # Save the instance ID for later use

    # Wait until all instances are running
    for instance_id in instances:
        instance = ec2_resource.Instance(instance_id)
        instance.wait_until_running()

    # Wait until all instances are accessible
    for instance_id in instances:
        instance = ec2_resource.Instance(instance_id)
        while not instance.public_ip_address:
            time.sleep(5)
            instance.reload()

    return instances

@app.route('/analyze', methods=['POST'])
def analyze():
    global results, selected_service, start_time
    results = []
    output_data = []
    audit_data = []
    minhistory = int(request.form['history'])
    shots = int(request.form['data_points'])
    signal_type = request.form['signal_type']
    days = int(request.form['days'])  # Convert to integer
    if selected_service != 'ec2':
        start_time = time.time()

    # Get stock data from Yahoo Finance
    today = date.today()
    decadeAgo = today - timedelta(days=1095)
    data_df = yf.download('NFLX', start=decadeAgo, end=today)

    # Convert the dataframe to a list of dictionaries
    data = []
    for row in data_df.itertuples():
        data.append({
            'Date': row.Index.to_pydatetime().strftime('%Y-%m-%d'),  # Convert datetime to string
            'Open': row.Open,
            'High': row.High,
            'Low': row.Low,
            'Close': row.Close,
            'Adj Close': row._5,
            'Volume': row.Volume,
            'Buy': 0,
            'Sell': 0
        })

    # Invoke the Lambda function
    payload = {
        'data': data,
        'minhistory': minhistory,
        'shots': shots,
        'days': days
    }
    
    
    if selected_service == 'lambda':
        lambda_url = 'https://0yu7zd36q4.execute-api.us-east-1.amazonaws.com/default/6766449_lambda'
        analysis_url = lambda_url
        response = requests.post(analysis_url, json=payload)
        if response.status_code == 200:
            response_data = response.json()
            if 'body' in response_data:
                results = json.loads(response_data['body'])
        
    elif selected_service == 'ec2':
        ec2_url = 'http://ec2-54-210-69-109.compute-1.amazonaws.com:5000/analyze'
        analysis_url = ec2_url
        response = requests.post(analysis_url, json=payload)
        if response.status_code == 200:
            results = response.json()
        
    else:
        # Invalid service selection, handle the error
        return redirect(url_for('home'))

    # Assign results to output_data
    output_data = results
    end_time = time.time()  # End the timer
    runtime = round(end_time - start_time, 2)

    # Process the results from the Lambda function
    mean_95 = sum([data['var95'] for data in results]) / len(results) if results else 0
    mean_99 = sum([data['var99'] for data in results]) / len(results) if results else 0


    # Add data to audit_data
    audit_data.append({
        'service': selected_service,
        'num_resources': len(resources),
        'minhistory': minhistory,
        'shots': shots,
        'signal_type': signal_type,
        'days': days,
        'var95_mean': mean_95,
        'var99_mean': mean_99,
        'runtime': runtime
    })

    # Upload the audit data to S3
    bucket_name = '6766449bucket'  # Replace with your S3 bucket name
    file_key = '6766449_audit.json'  # Name of the JSON file in S3

    # Retrieve existing audit data from S3
    existing_audit_data = []
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        existing_audit_data = json.loads(response['Body'].read())
    except s3_client.exceptions.NoSuchKey:
        pass

    # Combine existing and new audit data
    combined_audit_data = existing_audit_data + audit_data

    # Upload the updated audit data to S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=file_key,
        Body=json.dumps(combined_audit_data),
        ContentType='application/json'
    )

    chart_data = [['Signal Date', '95% Risk', '99% Risk', 'Mean 95% Risk', 'Mean 99% Risk']] + [
        [data['Buy_Date'], data['var95'], data['var99'], mean_95, mean_99] for data in results
    ]

    return render_template('output.html', chart_data=json.dumps(chart_data), output_data=output_data)

@app.route('/output')
def output():
    global results
    mean_95 = sum([result['var95'] for result in results]) / len(results) if results else 0
    mean_99 = sum([result['var99'] for result in results]) / len(results) if results else 0

    results_data = [
        ["Index", "95% Risk", "99% Risk", "Mean 95% Risk", "Mean 99% Risk"]
    ] + [
        [i, result['var95'], result['var99'], mean_95, mean_99] for i, result in enumerate(results)
    ]

    return render_template('output.html', results_data=json.dumps(results_data))


@app.route('/audit')
def audit():
    # Retrieve audit data from S3
    bucket_name = '6766449bucket'  # Replace with your S3 bucket name
    file_key = '6766449_audit.json'  # Name of the JSON file in S3

    audit_data = []
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        audit_data = json.loads(response['Body'].read())
    except s3_client.exceptions.NoSuchKey:
        pass

    return render_template('audit.html', audit_data=audit_data)


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    global results, audit_data, is_initialized, resources, selected_service, minhistory, shots, signal_type, days

    # Clear user input values
    minhistory = []
    shots = []
    signal_type = []
    days = []
    return render_template('home.html')


@app.route('/terminate', methods=['GET', 'POST'])
def terminate():
    global resources

    if selected_service == 'ec2':
        ec2_resource = boto3.resource('ec2', region_name='us-east-1')
        for instance_id in resources:
            ec2_resource.instances.filter(InstanceIds=[instance_id]).terminate()

    resources = []

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

