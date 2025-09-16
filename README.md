Team JnU_TrueNest Project - Voter API
Welcome to our Voter API project! This is a simple Flask-based application built for the Hackathon Preli by Team JnU_TrueNest. It’s designed to manage voter data with a clean API endpoint. Let’s dive into what this project is all about!
What’s Inside:

app.py: The main Flask app with the voter API logic.
Dockerfile: Sets up the Python environment in a Docker container.
docker-compose.yml: Configures the Docker service to run the app.
requirements.txt: Lists the Python dependencies (like Flask).

How to Run
We’ve made it easy to get started with Docker! Here’s what to do:

Install Docker: Make sure Docker Desktop is installed on your machine.
Clone or Use the ZIP: Get the project files (either clone the repo or use the jnu_truenest.zip).
Navigate to the Folder: Open your terminal and go to the project directory (e.g., cd C:\team_jnu).
Start the App:docker compose up -d --build


Test the API: Open your browser or use a tool like PowerShell:$body = @{ voter_id = 4; name = "David"; age = 20 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/voters" -Method Post -Headers @{"Content-Type"="application/json"} -Body $body

You should see a response with the voter data!

API Endpoint

POST /api/voters: Add a new voter.
Body: { "voter_id": int, "name": string, "age": int }
Response: Voter object with has_voted set to False by default.



Notes

The app runs on port 8000.
We’ve used Python 3.9 in the Docker image—keep that in mind if you tweak things!
Feel free to reach out if you hit any snags—we’re happy to help!

Thanks!
A huge thank you to the organizers GUCC & CSE Department, Green University Bangladesh for hosting this amazing Hackathon Preli! Your support and opportunity mean the world to us. Let’s make voting data management fun and easy together! 🚀
