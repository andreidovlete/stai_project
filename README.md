
# CSV Filter Web App

This is a Flask-based web application that allows users to upload a CSV file, apply various filters on the dataset, and view the filtered results in a paginated table.

---

## Features

- CSV upload with validation
- Data anomaly and warning detection
- Multiple filter types:
  - Date range
  - Anomaly and Warning flags
  - Anomaly percent probability
  - Age, weight, height, and IMC index range sliders
  - IMC category filters (Underweight, Obese, etc.)
  - Sex filters (Male, Female)
- Pagination (50 rows per page)
- Client-side checkbox handling with JavaScript
- Persistent filters via query parameters

---

## How to Run

1. **Install dependencies**:
   ```bash
   pip install flask pandas
   ```

2. **Start the app**:
   ```bash
   python app.py
   ```

3. **Visit in browser**:
   ```
   http://localhost:5000
   ```

---

## Run with Docker

You can run the app inside a Docker container for easier deployment:

### 1. Create a `Dockerfile`:

```dockerfile
# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy app files
COPY . /app

# Install dependencies
RUN pip install flask pandas

# Expose port
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]
```

### 2. Build and run the Docker container:

```bash
docker build -t csv-filter-app .
docker run -p 5000:5000 csv-filter-app
```

Then open: [http://localhost:5000](http://localhost:5000)

> Make sure your CSV files are accessible inside the container if you're deploying in production.

---

## File Structure

- `app.py` — Main Flask application handling upload, filtering, and rendering
- `upload.html` — Frontend HTML with form, checkboxes, sliders, and pagination
- `automatic_detection.py` — Contains `detect_anomalies_and_warnings` and `compute_anomaly_percent` used for processing data
- `/web/static/` — Contains CSS and JS files (not shown here)
- `/web/` — Contains `upload.html` template

---

## Filtering Logic

Filters are applied only when their corresponding checkboxes are selected. JavaScript syncs checkbox states to hidden inputs before GET requests.

Each filter parameter (e.g., `filter_by_age_range_chk`, `age_min`, `age_max`) is processed server-side and applied to the dataset using Pandas filtering.

---

## Notes

- Uploaded files are temporarily stored in memory as pickled DataFrames (`temp_id`).
- The app ensures all required parameters are passed to the template, even in error or fallback states.
- Compatible with Chrome, Edge, Firefox.

---

## Feedback

For improvements or bug reports, please open an issue or contact the developer.
