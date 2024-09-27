from supabase import create_client, Client, ClientOptions

url: str = "https://rxvuigbyexdarrlusojh.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4dnVpZ2J5ZXhkYXJybHVzb2poIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDA1MzI2MzQsImV4cCI6MjAxNjEwODYzNH0.74S-9Do20NbZLDuFAldxkS1fHEVHRTjCjOClOPE_psg"  # Replace with your anon or service key
supabase: Client = create_client(
    url, key, options=ClientOptions(auto_refresh_token=False))

# Sign in using user credentials
email = "cadewoolaway@outlook.com"
password = "Cade@1227"

# Authenticate the user
response = supabase.auth.sign_in_with_password({
    "email": email,
    "password": password
})

# Now you can interact with Supabase as an authenticated user
filepath = "map_temp.jpg"

with open(filepath, 'rb') as f:
    upload_response = supabase.storage.from_("weg_public").upload(
        f"webimgs/forecast_maps/{filepath}",
        file=f,
        file_options={"cache-control": "3600", "upsert": "true"}
    )

filepath = "map_windgusts.jpg"
with open(filepath, 'rb') as f:
    upload_response = supabase.storage.from_("weg_public").upload(
        f"webimgs/forecast_maps/{filepath}",
        file=f,
        file_options={"cache-control": "3600", "upsert": "true"}
    )

filepath = "map_winds.jpg"
with open(filepath, 'rb') as f:
    upload_response = supabase.storage.from_("weg_public").upload(
        f"webimgs/forecast_maps/{filepath}",
        file=f,
        file_options={"cache-control": "3600", "upsert": "true"}
    )

filepath = "FWR.jpg"
with open(filepath, 'rb') as f:
    upload_response = supabase.storage.from_("weg_public").upload(
        f"webimgs/forecast_maps/{filepath}",
        file=f,
        file_options={"cache-control": "3600", "upsert": "true"}
    )
