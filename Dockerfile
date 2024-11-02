FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the entry point to execute main.py with a command line argument
ENTRYPOINT ["python", "main.py"]

# Define the command line argument
CMD ["search_term"]
# build docker image once with:
# docker build -t steam_scraper .
# docker run steam_scraper your_search_term
# docker ps -a
# get the name of the container
# docker cp name_of_the_container:/app/data.json C:\Users\radde\Downloads\data.json
