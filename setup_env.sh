#!/bin/bash
# Shell script to setup environment variables for macOS/Linux
# This creates a .env file with the required database connection settings

cat > .env << EOF
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=home_db
MYSQL_USER=db_user
MYSQL_PASSWORD=6equj5_db_user
EOF

echo "✅ Created .env file with database connection settings"
echo ""
echo "Next steps:"
echo "1. Start MySQL: docker-compose -f docker-compose.initial.yml up --build -d"
echo "2. Install Python dependencies: pip install -r requirements.txt"
echo "3. Run ETL: cd scripts && python3 etl.py"

