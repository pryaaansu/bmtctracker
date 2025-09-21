#!/usr/bin/env python3
"""
Database management script for BMTC Transport Tracker
"""
import sys
import argparse
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from migrations.create_tables import create_tables, drop_tables
from migrations.seed_data import seed_database
from app.core.database import check_database_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Database management for BMTC Transport Tracker")
    parser.add_argument("command", choices=["create", "drop", "seed", "reset", "health"], 
                       help="Database command to execute")
    parser.add_argument("--force", action="store_true", 
                       help="Force operation without confirmation")
    
    args = parser.parse_args()
    
    if args.command == "health":
        if check_database_health():
            logger.info("✅ Database connection is healthy")
            sys.exit(0)
        else:
            logger.error("❌ Database connection failed")
            sys.exit(1)
    
    elif args.command == "create":
        logger.info("Creating database tables...")
        if create_tables():
            logger.info("✅ Database tables created successfully")
        else:
            logger.error("❌ Failed to create database tables")
            sys.exit(1)
    
    elif args.command == "drop":
        if not args.force:
            confirm = input("⚠️  This will DROP ALL TABLES. Are you sure? (yes/no): ")
            if confirm.lower() != "yes":
                logger.info("Operation cancelled")
                sys.exit(0)
        
        logger.info("Dropping database tables...")
        if drop_tables():
            logger.info("✅ Database tables dropped successfully")
        else:
            logger.error("❌ Failed to drop database tables")
            sys.exit(1)
    
    elif args.command == "seed":
        logger.info("Seeding database with sample data...")
        if seed_database():
            logger.info("✅ Database seeded successfully")
        else:
            logger.error("❌ Failed to seed database")
            sys.exit(1)
    
    elif args.command == "reset":
        if not args.force:
            confirm = input("⚠️  This will DROP ALL TABLES and recreate them. Are you sure? (yes/no): ")
            if confirm.lower() != "yes":
                logger.info("Operation cancelled")
                sys.exit(0)
        
        logger.info("Resetting database...")
        
        # Drop tables
        if not drop_tables():
            logger.error("❌ Failed to drop tables")
            sys.exit(1)
        
        # Create tables
        if not create_tables():
            logger.error("❌ Failed to create tables")
            sys.exit(1)
        
        # Seed data
        if not seed_database():
            logger.error("❌ Failed to seed database")
            sys.exit(1)
        
        logger.info("✅ Database reset completed successfully")

if __name__ == "__main__":
    main()