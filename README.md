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
- [Deployment](#deployment)
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
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
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

#### Build Docker Image

```bash
docker build -t your-dockerhub-username/weather-station-app .
```

#### Run Docker Container with Environment Variables

```bash 
docker run --env-file .env -p 5000:5000 your-dockerhub-username/weather-station-app
``` 

Access the application at [http://localhost:5000](http://localhost:5000).

## Routes

[/initialize_tokens](http://localhost:5000/initialize_tokens): Initialize or update access tokens and credentials.  
[/show_data_table](http://localhost:5000/show_data_table): View all weather station and module data.  
[/show_all_measurements](http://localhost:5000/show_all_measurements): View all measurement data for the weather stations.  
[/get_data](http://localhost:5000/get_data): Fetches current data from the Netatmo API.  
[http://localhost:8000](http://localhost:8000): Run phpMyAdmin  

## Deployment
This application is ready for deployment on Docker Hub and GitHub.

### Push to GitHub

```bash
git push -u origin main
```

#### Push Docker Image to Docker Hub

```bash
docker login
docker tag your-dockerhub-username/weather-station-app:latest your-dockerhub-username/weather-station-app:latest
docker push your-dockerhub-username/weather-station-app:latest
```

## Contributing
If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are welcome.
