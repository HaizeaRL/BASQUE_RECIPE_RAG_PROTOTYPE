# Use the official Python 3.7 image from Docker Hub
FROM python:3.7

# Set the working directory inside the container
WORKDIR /usr/local/app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the required packages from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .


# Set the default command to start a bash shell
CMD ["/bin/bash"]