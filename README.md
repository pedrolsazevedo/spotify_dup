# Spotify Playlist Analyzer

This Python script fetches information about a Spotify playlist, analyzes it, and generates a JSON report with details such as tracks, artists, and duplicates.

## Prerequisites

Before running the script, make sure you have the following:

- Python 3 installed
- Spotify Developer account
- Spotify playlist URL

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/spotify-playlist-analyzer.git
```

1. Install the required Python packages:
```bash
pip install -r requirements.txt
```

1. Set up environment variables for your Spotify Client ID and Client Secret:  
```bash
export SPOTIFY_CLIENT_ID='your_client_id'
export SPOTIFY_CLIENT_SECRET='your_client_secret'
```

## Usage
1. Run the script by executing the main.py file:
```bash
python main.py
```


run as container:
```bash
docker run -it --rm -v $(pwd):/app --name python --hostname python-container python bash
```

## Docker

docker pull python
docker run -it --rm -v $(pwd):/app --name python --hostname python-container python bash