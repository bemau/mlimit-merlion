CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set uuid
ALTER TABLE salesforce.measure_config_type__c ALTER COLUMN externalid__c SET DEFAULT uuid_generate_v4();
ALTER TABLE salesforce.measureconfig__c ALTER COLUMN externalid__c SET DEFAULT uuid_generate_v4();
ALTER TABLE salesforce.measure__c ALTER COLUMN externalid__c SET DEFAULT uuid_generate_v4();
ALTER TABLE salesforce.forecaster__c ALTER COLUMN externalid__c SET DEFAULT uuid_generate_v4();
ALTER TABLE salesforce.configauth__c ALTER COLUMN externalid__c SET DEFAULT uuid_generate_v4();

-- Convert column data type from float8 to int4
ALTER TABLE salesforce.measure__c ALTER COLUMN max_value__c TYPE int;
ALTER TABLE salesforce.measure__c ALTER COLUMN remaining_value__c TYPE int;
ALTER TABLE salesforce.measureconfig__c ALTER COLUMN max_value__c TYPE int;
ALTER TABLE salesforce.forecaster__c ALTER COLUMN yhat__c TYPE int;
ALTER TABLE salesforce.forecaster__c ALTER COLUMN fact__c TYPE int;
ALTER TABLE salesforce.forecaster__c ALTER COLUMN yhat_upper__c TYPE int;
ALTER TABLE salesforce.forecaster__c ALTER COLUMN yhat_lower__c TYPE int;
