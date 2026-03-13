-- referenced by sql_task
INSERT INTO catalog.schema.target_table
SELECT *
FROM catalog.schema.source_table
WHERE event_date = date(:run_date);