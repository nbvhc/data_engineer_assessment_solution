#!/bin/bash
# Shell script to setup environment variables for macOS/Linux
# This creates a .env file with database connection settings
# Values should match those in docker-compose.initial.yml

cat > .env << EOF
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=<database_name>
MYSQL_USER=<database_user>
MYSQL_PASSWORD=<database_password>
EOF

echo "Created .env file template"
echo ""
echo "IMPORTANT: Update .env file with actual credentials from docker-compose.initial.yml"
echo ""
echo "Next steps:"
echo "1. Edit .env file with correct database credentials"
echo "2. Start MySQL: docker-compose -f docker-compose.initial.yml up --build -d"
echo "3. Install Python dependencies: pip install -r requirements.txt"
echo "4. Run ETL: cd scripts && python3 etl.py"

