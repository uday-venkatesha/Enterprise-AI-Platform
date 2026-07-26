# Start from a small official Python image.
FROM python:3.12-slim

# All following commands run inside /code in the image.
WORKDIR /code

# Copy ONLY requirements first, then install. Docker caches this layer, so
# rebuilds are fast unless your dependencies actually change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the source. (Changing source won't bust the dependency cache above.)
COPY src ./src

# Make the "app" package importable.
ENV PYTHONPATH=/code/src

# Document the port the app listens on.
EXPOSE 8000

# The command that runs when the container starts.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]