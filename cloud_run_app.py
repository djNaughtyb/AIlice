#!/usr/bin/env python3
"""
Cloud Run wrapper for AIlice Flask application.
This script adapts AIlice to work with Google Cloud Run requirements.
"""
import os
import sys
import logging
from ailice.app.app import app, Init, config, AILICE_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for Cloud Run deployment.
    """
    # Get port from environment (Cloud Run provides this)
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('AILICE_HOST', '0.0.0.0')
    
    # Initialize configuration
    config_file = os.environ.get('AILICE_CONFIG_FILE', AILICE_CONFIG)
    logger.info(f"Initializing AIlice with config: {config_file}")
    
    try:
        # Initialize AIlice configuration
        config.Initialize(configFile=config_file)
        
        # Update config with environment variables if present
        config_updates = {}
        
        if os.environ.get('AILICE_MODEL_ID'):
            config_updates['modelID'] = os.environ.get('AILICE_MODEL_ID')
        
        if os.environ.get('AILICE_TEMPERATURE'):
            config_updates['temperature'] = float(os.environ.get('AILICE_TEMPERATURE'))
        
        if os.environ.get('AILICE_CONTEXT_WINDOW_RATIO'):
            config_updates['contextWindowRatio'] = float(os.environ.get('AILICE_CONTEXT_WINDOW_RATIO'))
        
        if config_updates:
            config.Update(config_updates)
            logger.info(f"Updated config with environment variables: {config_updates}")
        
        # Initialize AIlice services and app
        Init()
        
        # Initialize database if DATABASE_URL is provided
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            try:
                from ailice.common.ADatabase import initialize_database
                initialize_database(database_url)
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.warning(f"Database initialization failed (continuing anyway): {e}")
        
        # Start the Flask application
        logger.info(f"Starting AIlice on {host}:{port}")
        app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        logger.critical(f"Failed to start AIlice: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
