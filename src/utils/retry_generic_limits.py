# -*- coding: utf-8 -*-
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
''' retry generic limits'''
from sqlalchemy import exc
import pandas as pd
from src.models.measure_config import MeasureConfig
from src.models.measure import Measure
from src.models import db_session
from src.config.logger import LoggerClass
from src.config.salesforce import SalesforceConnection
logging = LoggerClass.instance()
Session = db_session()


def retry_generic_limits(freq):
    ''' Generic SOQL query to get all measures with limits '''
    logging.logger.info('process started')
    # config_limits = Session.query(
    #     MeasureConfig.name).filter(MeasureConfig.active == True).all()
    source = 'soql_count'
    try:
        df_limits = pd.DataFrame(Session.query(
            MeasureConfig).filter(MeasureConfig.active == True,
                                MeasureConfig.source == source,
                                MeasureConfig.frequency == freq).all())
    except exc.SQLAlchemyError as exc_error:
        logging.logger.error(exc_error)
        raise
    except Exception as error:
        logging.logger.error(error)
        raise
        
    if len(df_limits.index) > 0:
        sf = SalesforceConnection.instance()
        for i in range(len(df_limits)):
            query = df_limits.loc[i, "query"]
            if query:
                # manipulate the session instance (optional)
                record = sf.session.query(
                    query
                )
                logging.logger.debug('record %s', record)
                df_limits.loc[i, 'remaining_value'] =\
                    df_limits['max_value'].loc[i] \
                    - record['totalSize']
        df_limits.drop(df_limits.columns.difference(
            ['remaining_value', 'name', 'max_value', 'sfid']),
            1, inplace=True)

        # df_limits.dropna(inplace=True)
        df_limits['limitname'] = df_limits['name'].map(
            df_limits.set_index("name")["sfid"])
        df_limits = df_limits.dropna()
        print('----------------------------------------------------')
        print(df_limits.head(3).T)

        try:
            Session.bulk_insert_mappings(
                Measure, df_limits.to_dict(orient="records"))
            Session.commit()
            logging.logger.debug('added records head(3) \n %s', df_limits.head(3).T)
            logging.logger.debug('added records shape %s', df_limits.shape)
            # return df_limits
        except exc.SQLAlchemyError as exc_error:
            Session.rollback()
            logging.logger.error(exc_error)
            raise
        finally:
            Session.close()
    else:
        logging.logger.info(
            'Generic limits are not configured in Config Limit')


if __name__ == "__main__":
    main()
