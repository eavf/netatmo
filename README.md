# Weather Station Data Monitoring Application

A Flask-based web application for monitoring weather data from Netatmo stations. It is designed for learning and practicing Python, Flask, and the API.  
This application retrieves and stores weather data from the Netatmo API, with the functionality to view station data, modules, and measurements in an easy-to-navigate interface. This application comes with a built-in SQL server and myPHPadmin. However, there is nothing to stop you from using your own server, just change the database server configuration in app.py and the db section in docker-compose.yml.
This is the first part of the project, the second part will deal with ML and using AI for analysis and prediction.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
  - [Environment Variables](#environment-variables)
  - [Running Locally](#running-locally)
  - [Running with Docker](#running-with-docker)
- [Routes](#routes)
- [Disclaimer](#disclaimer)
- [Contributing](#contributing)

## Features

- **Token Initialization**: Initialize or update access and refresh tokens for the Netatmo API.
- **Weather Data Viewing**: View weather station data, modules, and measurements from Netatmo stations.
- **UI for Monitoring**: A web interface to select and display station-specific data.
- **Dockerized**: Easily deployable as a Docker container.

## Requirements

- Python 3.9+
- [Flask](https://flask.palletsprojects.com/)
- [Docker](https://www.docker.com/) (optional, for containerized deployment)

## Setup

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```plaintext
ACCESS_TOKEN=            # Netatmo API access token
REFRESH_TOKEN=           # Netatmo API refresh token
CLIENT_ID=               # Netatmo API client ID
CLIENT_SECRET=           # Netatmo API client secret
TOKEN_EXPIRY=            # Unix timestamp for token expiry
TOKEN_URL=https://api.netatmo.com/oauth2/token
API_URL=https://api.netatmo.com/api/getstationsdata?get_favorites=true
```

For an example, refer to .env.example.

### Running Locally

#### Clone the Repository

```bash
git clone https://github.com/eavf/netatmo.git
cd netatmo
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Run the Application

```bash
flask run
```
Access the application at [http://localhost:5000](http://localhost:5000).

### Running with Docker

For projects that have multiple services or containers (like this application with a database and the Flask application), Docker Compose can help manage them in a single configuration file. We will now look at how to download and run this application, along with its MySQL database and phpMyAdmin interface, using a pre-built Docker image from DockerHub.

#### Prerequisites
Ensure you have Docker and Docker Compose installed on your system. You can check if it’s installed by running:
```bash
docker --version
docker-compose --version
```
If it’s not installed, you can install it by following the official Docker Compose installation guide.

#### Setting Up Docker Compose
1. Create docker-compose.yml file in the root of the project directory with the following configuration:

```bash
version: '3.8'

services:
  app:
    image: eavfeavf/weather-station-app:latest  # Použitie obrazu z DockerHub
    container_name: flask_app
    ports:
      - "5000:5000"
    environment:
      - ACCESS_TOKEN=${ACCESS_TOKEN}
      - REFRESH_TOKEN=${REFRESH_TOKEN}
      - MYSQL_HOST=db
      - MYSQL_USER=vovo
      - MYSQL_PASSWORD=vovo_pass_sql
      - MYSQL_DATABASE=vovo
    depends_on:
      - db

  db:
    image: mysql:8.0
    container_name: mysql_db
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: vovo
      MYSQL_USER: vovo
      MYSQL_PASSWORD: vovo_pass_sql
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql  # Initializes the DB schema

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    container_name: phpmyadmin_natatmo
    environment:
      PMA_HOST: db  # Links to the `db` service
      MYSQL_ROOT_PASSWORD: root_password  # Root password of MySQL
    ports:
      - "8080:80"  # Expose phpMyAdmin on localhost:8080
    depends_on:
      - db

volumes:
  mysql_data:
```
2. Or clone github repository.
This repository contains the necessary docker-compose.yml (docker-compose_local.yml) file to orchestrate the multi-container setup:
```bash
git clone https://github.com/eavf/netatmo.git
cd netatmo
```
Replace yourpassword (all passwords) with a secure password, and optionally make sure the .env file exists in the root directory with your API credentials and other environment variables. You can also add these via the web menu after running the application.

#### Start the application using Docker Compose
Ensure you are in the folder containing the docker-compose.yml file, then run:

```bash
docker-compose pull     # to pull image from dockerhub
docker-compose up -d    # to run app
```
If you prefer to build local image, so go into the app folder and do it by changing the image instruction in the app:
```bash
build: .
```
and buil it locally by:
```bash
docker-compose up --build
```
Or without --built if you didnt change image configuration.  
Access the application at [http://localhost:5000](http://localhost:5000).

## Routes
[/initialize_tokens](http://localhost:5000/initialize_tokens): Initialize or update access tokens and credentials.  
[/show_data_table](http://localhost:5000/show_data_table): View all weather station and module data.  
[/show_all_measurements](http://localhost:5000/show_all_measurements): View all measurement data for the weather stations.  
[/get_data](http://localhost:5000/get_data): Fetches current data from the Netatmo API.  
[http://localhost:8000](http://localhost:8000): Run phpMyAdmin  
The links will only work on the computer running the application. If you want to run it on a server, you will need to modify the configuration of the server itself, adjust the ports to which the communication is eventually redirected and, especially in the case of a production server, modify the application to run in a publicly accessible location (see the Flash documentation).  
Note that if you have not previously stored data in the database, any listing from it will be empty.

## Disclaimer
The application requires a development account on netatmo.com, where you can also find the relevant documentation for the Netatmo API, create the necessary keys and get the necessary devices such as weather stations, thermostat heads and other interesting devices to build a smart home. 
This is a development project, not a production application, so if you don't know the difference, don't use it on the Internet.


## Contributing
If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are welcome.
