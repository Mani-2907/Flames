# FLAMES

## Run locally

From the project root, install the Python dependencies and start the Flask server:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe Backend\app.py
```

Open <http://127.0.0.1:5000/>. Calculations are saved to `Backend/flames.db`.

## Connect Firebase Firestore

Firestore syncing is optional. Without Firebase credentials, results are still saved in the local SQLite database.

1. In the Firebase console, open project `flames-497e4` (or update `FIREBASE_PROJECT_ID` if using another project) and create a Cloud Firestore database.
2. In Google Cloud Console for the same project, enable the Cloud Firestore API.
3. Create a service account with permission to write Firestore data, then download its JSON key. Keep the key private and save it as `Backend/firebase-service-account.json`.
4. Copy `.env.example` to `.env` in the project root. Confirm `FIREBASE_PROJECT_ID` matches the Firebase project and `FIREBASE_SERVICE_ACCOUNT_FILE` points to the downloaded key.
5. Restart Flask. New calculations will be written to the Firestore `calculations` collection and saved locally in SQLite.

Each Firestore document stores both entered names, the FLAMES code and result, a UTC timestamp, and the local SQLite record ID. Only enable cloud saving if you have permission to store those names in the Firebase project. The Firebase web SDK snippet is not needed: the backend uses the Admin SDK and keeps service-account credentials off the webpage.

## Deploy publicly to Google Cloud Run

The repository includes a Dockerfile for Cloud Run. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install), then open a new terminal and run these commands from the project root:

```powershell
gcloud auth login
gcloud config set project flames-497e4
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com
gcloud iam service-accounts create flames-runtime
gcloud projects add-iam-policy-binding flames-497e4 --member="serviceAccount:flames-runtime@flames-497e4.iam.gserviceaccount.com" --role="roles/datastore.user"
gcloud run deploy flames --source . --region us-central1 --allow-unauthenticated --service-account flames-runtime@flames-497e4.iam.gserviceaccount.com --set-env-vars FIREBASE_PROJECT_ID=flames-497e4
```

Create the Firestore database in the Firebase console before deploying. Cloud Run uses its attached runtime service account, so do not upload a service-account JSON key. The `--allow-unauthenticated` option makes the website public; the API validates input but is not restricted to signed-in users. Cloud Run's local filesystem is temporary, so Firestore is the persistent database in production; SQLite is only a local fallback.

## Alternative: deploy on Render

The `render.yaml` blueprint runs this Flask app as a Render web service. To deploy it, push the project to a public GitHub repository, open the [Render Blueprint dashboard](https://dashboard.render.com/blueprint/new), connect the repository, and create the service. The free service may spin down when idle and its local filesystem is temporary, so configure Firestore for persistent calculation records.

In the Render service settings, add a secret file named `firebase-service-account.json` containing the Firebase service-account JSON. The blueprint points `FIREBASE_SERVICE_ACCOUNT_FILE` at Render's private secret-file path. Keep this key out of GitHub. The service uses project `flames-497e4`; update `render.yaml` if deploying to another Firebase project.