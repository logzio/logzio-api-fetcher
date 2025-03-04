FROM python:3.14.0a5-slim
WORKDIR /app

# python settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set user as non root
RUN chown nobody:nogroup /app
USER nobody

# Copy the program to /src
COPY --chown=nobody:nogroup /src ./src

# Run the program
ENTRYPOINT ["python", "-m", "src.main"]