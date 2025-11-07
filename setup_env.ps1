# PowerShell script to setup environment variables for Windows
# This creates a .env file with the required database connection settings

$envContent = @"
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=home_db
MYSQL_USER=db_user
MYSQL_PASSWORD=6equj5_db_user
"@

$envContent | Out-File -FilePath .env -Encoding utf8 -NoNewline

Write-Host "✅ Created .env file with database connection settings" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start MySQL: docker-compose -f docker-compose.initial.yml up --build -d"
Write-Host "2. Install Python dependencies: pip install -r requirements.txt"
Write-Host "3. Run ETL: cd scripts && python etl.py"

