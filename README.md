# Weather Station Data Monitoring Application

A Flask-based web application to monitor weather data from Netatmo stations. This app fetches and stores weather data from the Netatmo API, with functionalities for viewing station data, modules, and measurements in an easy-to-navigate interface.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
  - [Environment Variables](#environment-variables)
  - [Running Locally](#running-locally)
  - [Running with Docker](#running-with-docker)
- [Routes](#routes)
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

For projects that have multiple services or containers (like this application with a database and the Flask application), Docker Compose can help manage them in a single configuration file. This guide explains how to download and run the this application, along with its MySQL database and phpMyAdmin interface, using a pre-built Docker image from DockerHub.

#### Prerequisities
Ensure you have Docker and Docker Compose installed on your system. You can check if it’s installed by running:
```bash
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
This repository contains the necessary docker-compose.yml file to orchestrate the multi-container setup:
```bash
git clone https://github.com/eavf/netatmo.git
cd netatmo
```
Replace yourpassword (all passwords) with a secure password, and make sure the .env file is present in the root directory with your API credentials and other environment variables. You can add them as well via web menu after having run the App.

#### Start the application using Docker Compose
Ensure you are in the folder containing the docker-compose.yml file, then run:

```bash
docker-compose pull     # to pull image from dockerhub
docker-compose up -d    # to run app
```
If you prefer to build localy image, so do it by changing image instruction in app:
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
(links will work only on computer where is running app.)
[/initialize_tokens](http://localhost:5000/initialize_tokens): Initialize or update access tokens and credentials.  
[/show_data_table](http://localhost:5000/show_data_table): View all weather station and module data.  
[/show_all_measurements](http://localhost:5000/show_all_measurements): View all measurement data for the weather stations.  
[/get_data](http://localhost:5000/get_data): Fetches current data from the Netatmo API.  
[http://localhost:8000](http://localhost:8000): Run phpMyAdmin  

## Contributing
If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are welcome.
