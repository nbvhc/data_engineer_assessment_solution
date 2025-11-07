# PowerShell script to setup environment variables for Windows
# This creates a .env file with database connection settings
# Values should match those in docker-compose.initial.yml

$envContent = @"
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=<database_name>
MYSQL_USER=<database_user>
MYSQL_PASSWORD=<database_password>
"@

$envContent | Out-File -FilePath .env -Encoding utf8 -NoNewline

Write-Host "Created .env file template" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Update .env file with actual credentials from docker-compose.initial.yml" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with correct database credentials"
Write-Host "2. Start MySQL: docker-compose -f docker-compose.initial.yml up --build -d"
Write-Host "3. Install Python dependencies: pip install -r requirements.txt"
Write-Host "4. Run ETL: cd scripts && python etl.py"

