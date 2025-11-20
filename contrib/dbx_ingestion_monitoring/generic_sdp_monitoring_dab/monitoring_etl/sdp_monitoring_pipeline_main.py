import dlt
import sys
import logging

sys.path.append("../../lib")

from dbx_ingestion_monitoring.common_ldp import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Starting Generic SDP Monitoring ETL Pipeline")

# Pipeline parameters

conf = Configuration(spark.conf)
pipeline = MonitoringEtlPipeline(conf, spark)
pipeline.register_base_tables_and_views(spark)