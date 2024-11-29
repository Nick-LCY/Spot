from .handlers import *
from AEFM.manager import manager
from AEFM import set_config_file, set_log_level

set_config_file("e2e_predictor/collect/collect_e2e.yaml")
set_log_level("info")

manager.run()
