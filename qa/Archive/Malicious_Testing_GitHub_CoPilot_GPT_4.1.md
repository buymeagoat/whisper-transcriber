# Malicious Testing Results

---

Test: Application startup with missing database directory
Results: Application failed to start. Error: (sqlite3.OperationalError) unable to open database file. The container did not create the required /app/data directory, resulting in a startup block.

Test: Attempt to create /app/data directory from host
Results: Permission denied. Host cannot create /app/data inside the container context. Application still fails to start due to missing database file.
