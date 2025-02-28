# TITLE

-   **Author**: Haizea Rumayor Lazkano
-   **Last update**: February 2025

------------------------------------------------------------------------

## Installation and Run Steps

To get started with this project, please follow these steps:

### Prerequisites

1. **Install Docker**: Ensure Docker is installed on your machine. You can download and install it from the [Docker website](https://www.docker.com/products/docker-desktop).

### Configuration for Matplotlib

To use Matplotlib in a Docker container with GUI support, you'll need to configure X11 forwarding on your Windows machine. Follow these instructions:

1. **Install XLaunch**:
   - Download and install **XLaunch** from the [Xming website](https://sourceforge.net/projects/xming/).
   - Launch XLaunch and choose **"Multiple windows"** when prompted.
   - Set the display number to **0**.
   - Select **"Start No client"**.
   - Choose **"Native OpenGL"**.
   - Check **"No access control"** to allow connections.

2. **Get Your Windows IP Address**:
   - Open Command Prompt and run the following command to find your IP address:
     ```bash
     ipconfig
     ```
   - Note the IPv4 Address (e.g., `192.168.1.100`).

### Building the Docker Image

1. **Navigate to the Project Directory**:
   Open your terminal and navigate to the root directory of the project where the `Dockerfile` is located.

2. **Build the Docker Image**:
   Run the following command to build the Docker image.  Replace `<app>` with corresponding value::
   ```bash
   docker build -t <app> .
   ```
2. **Run the Docker Image**:
    Replace `<app>` with corresponding value:
    ```bash
    docker run -it <app>
    ```
3. **Navigate to corresponding script and run the script**:
   First, you'll need to create the database using `create_data_base.py`, which involves categorizing wines and simulating users and their wine preferences:
    ```bash
    cd src
    python create_data_base.py
    ```

   Once the database is created, you can run the `main.py` script as many times as needed to generate recommendations:
   ```bash
    cd src
    python main.py
   ```
4. **Retrieve resuts locally**
   The results are saved in the `report` folder within the Docker container. 
   
   To retrieve the PDF file, open a command prompt, identify the running Docker container:
    ```bash
    docker ps
   ```
   Navigate to the Project Directory, and copy the file from the container to your local replacing `<docker_instance>` with corresponding value.
   ```bash
    docker cp <docker_instance>:/usr/local/app/report .
   ```