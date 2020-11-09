import os
import yaml
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(module)s:%(levelname)s:%(message)s'
)

app_dir = os.path.dirname(os.path.realpath(__file__))
conf_path = os.getenv('APP_CONF') or os.path.join(app_dir, 'config.yaml')
with open(conf_path) as f:
    config = yaml.safe_load(f)
    logging.info('loaded config from "%s"', conf_path)


