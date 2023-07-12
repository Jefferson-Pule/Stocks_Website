FROM gcr.io/my-stocks-website-25351839/myimage:latest  
# THIS LINE SHOULD HAPPEN BEFORE THE DOCKER FILE IS RUN "FROM gcr.io/%PROJECT%/myimage:latest"

USER root

RUN apt-get update && apt-get install -y gnupg

RUN apt-get update \
    && apt-get install -y curl apt-transport-https \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools unixodbc-dev \
    && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc 

USER cnb