CREATE OR REFRESH STREAMING TABLE parsed_documents_text
COMMENT 'Extracted text content from parsed documents with error handling'
AS (
  WITH error_documents AS (
    SELECT
      path,
      NULL AS text,
      try_cast(parsed:error_status AS STRING) AS error_status,
      parsed_at
    FROM STREAM(parsed_documents_raw)
    WHERE try_cast(parsed:error_status AS STRING) IS NOT NULL
  ),
  success_documents AS (
    SELECT
      path,
      concat_ws(
        '\n\n',
        transform(
          CASE
            WHEN try_cast(parsed:metadata:version AS STRING) = '1.0'
            THEN try_cast(parsed:document:pages AS ARRAY<VARIANT>)
            ELSE try_cast(parsed:document:elements AS ARRAY<VARIANT>)
          END,
          element -> try_cast(element:content AS STRING)
        )
      ) AS text,
      NULL AS error_status,
      parsed_at
    FROM STREAM(parsed_documents_raw)
    WHERE try_cast(parsed:error_status AS STRING) IS NULL
  )
  SELECT * FROM success_documents
  UNION ALL
  SELECT * FROM error_documents
);