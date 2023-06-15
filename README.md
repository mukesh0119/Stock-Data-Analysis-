# Stock-Data-Analysis-
Stock Data Analysis using Monte Carlo Method and Scalable Services 

This project presents an illustration of of applying the NIST 800-145 principles to a real-world scenario. The system analyses stock data using the Monte Carlo method and scalable service. 

This cloud-based stock data analysis system offers enhanced security, privacy, and scalability by implementing the NIST SP 800-145 principles.

Using the guidance given, users can easily calculate profit or loss from stock data and obtain comprehensive results on the output page. The backend framework of the system makes use of AWS EC2 and Lambda capabilities, ensuring optimal resource allocation and enhancing computational capabilities as necessary.In addition, the system's frontend framework is implemented using Google App Engine, which offers a stable and scalable platform for seamless user interaction.

## System Component Interactions
The user interacts with the Google App Engine-hosted frontend application.The user interface requires the selection of the number of resources and services for the analysis, followed by the number of days to verify profit, minhistory length, signal type, and shots. The interface of Google App Engine communicates with the Amazon API Gateway. It submits the user's analysis requirements to the API Gateway as a request. Based on the request, the API Gateway initiates AWS Lambda functions or EC-2. It forwards the analysis requirements for computation to the Lambda functions or EC-2. The data is processed by EC2 instances or lambda functions, which then return the results to the API Gateway. Through the API gateway, both Lambda functions and EC2 instances can store analysis results in an Amazon S3 container. The results, including buy/sell signals, profit/loss calculations, and statistical measurements, are securely stored in S3 for future review. The API Gateway returns the retrieved analysis results to the Google App Engine-hosted frontend application. Through the user interface, the frontend application presents the analysis results to the users. The outcomes are presented as a Google chart and a table containing all result values.

