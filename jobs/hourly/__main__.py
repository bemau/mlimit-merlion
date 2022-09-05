# -*- coding: utf-8 -*-
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
''' init file '''
from ast import Not
from logging import raiseExceptions
import traceback
from src.config.logger import LoggerClass
import src.config as config
from worker import conn
import time
import sys
from memory_profiler import profile
from rq import Queue
from jobs.hourly.predict_rest_limits import predict_rest_limits
from src.utils.retry_rest_api_resource_limits import retry_rest_api_resource_limits
from src.utils.retry_generic_limits import retry_generic_limits
from src.config.error import NoSalesforceConnection
import src.utils.database as utils_db
logging = LoggerClass.instance()


@profile
def calculate_memory(measure,freq, train_only):
    """Calculate Memory
    profile is a python module for monitoring memory consumption of a process
    Args:
        measure ([List]): list of event rest limits
    """
    predict_rest_limits(measure,freq, train_only)


if __name__ == '__main__':
    """ Schedule this job to feed the model
    """
    train_only = False
    freq = None
    
    if "--train-only" in sys.argv:
        train_only = True
    if "--freq-hourly" in sys.argv:
        freq = 'H'
    if "--freq-daily" in sys.argv:
        freq = 'D'
    
    
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    start_time = time.time()
    logging.logger.info('Start jobs process at %s', current_time)
    logging.logger.debug('WORKER_TYPE %s', config.WORKER_TYPE)
    logging.logger.debug('Argument List  %s', str(sys.argv))
    if (config.RETRY_DATA_FROM_SF == 'True' and train_only == False):
        logging.logger.debug('Start retrieving Salesforce Org limits...')
        try:
            if freq is not None:
                retry_rest_api_resource_limits(freq)
                retry_generic_limits(freq)
            else:
                raise Exception('Frequency not defined')
        except NoSalesforceConnection as no_salesforce_connection:
            logging.logger.error(no_salesforce_connection)
    for variate in utils_db.get_active_measure_config(freq):
        measure_name = variate[0]
        measure_freq = variate[1]
        logging.logger.debug(
            'Start worker variate %s frequency %s train %s' % (measure_name,measure_freq, train_only))
        if int(config.WORKER_TYPE) == 1:
            calculate_memory(measure_name,measure_freq, train_only)
            end_time = round(time.time() - start_time, 2)
            logging.logger.info('End jobs process took %s secs', end_time)
        elif int(config.WORKER_TYPE) == 2:
            q = Queue('low', connection=conn)
            try:
                dar = q.enqueue(predict_rest_limits,
                                # depends_on=gl,
                                ttl='6h',
                                failure_ttl='5d',
                                job_timeout='2h',
                                kwargs={
                                    'measure': measure_name,
                                    'freq': measure_freq,
                                    'train_only': train_only
                                })
            except Exception as e:
                traceback.print_exc()
                logging.logger.error(e)
                raise
        else:
            logging.logger.error('Worker Type not supported %s', config.WORKER_TYPE)
