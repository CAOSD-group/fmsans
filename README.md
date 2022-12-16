# fm_solver
FM solver is a solver for feature models that implement analysis operations without the need of a SAT or BDD solver.

## Configuration
The following parameters are configurable in the application:

`config.yml` file:
To activate/deactivate the Timer in charge of calculating the execution time of several functionalities, set the `timer_enabled` param to `yes/no` (default `yes`):
- `timer_enabled: yes`

`logging_config.yml` file:
To completely activate/deactivate the loggers, set the `disabled` param to `yes/no` (default `no`), for each logger you want to activate/deactivate:
- `disabled: yes`

To change the log LEVEL, change the `level` param to `DEBUG` or `INFO`. Currently, only the `main_logger` is configurable.
- `level: DEBUG`

To change the output file for the logs, change the `filename` param for each logger.
- `filename: fm_solver.log`

