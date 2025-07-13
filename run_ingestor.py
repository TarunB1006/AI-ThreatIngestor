#!/usr/bin/env python3
"""
ThreatIngestor runner script.

This script provides a simple way to run ThreatIngestor with a configuration file.
"""

import sys
import argparse
from loguru import logger

# Import the main ThreatIngestor class
from threatingestor import Ingestor


def main():
    """Main entry point for the ThreatIngestor runner."""
    parser = argparse.ArgumentParser(
        description="Run ThreatIngestor with the specified configuration file"
    )
    parser.add_argument(
        "--config", 
        required=True, 
        help="Path to the ThreatIngestor configuration YAML file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure basic logging if debug is requested
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    try:
        # Create and run the ThreatIngestor instance
        logger.info(f"Starting ThreatIngestor with config: {args.config}")
        app = Ingestor(args.config)
        app.run()
        logger.info("ThreatIngestor completed successfully")
        
    except KeyboardInterrupt:
        logger.info("ThreatIngestor stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"ThreatIngestor failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
