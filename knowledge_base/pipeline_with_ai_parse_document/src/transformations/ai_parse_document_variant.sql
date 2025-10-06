CREATE STREAMING TABLE parsed_documents_raw
TBLPROPERTIES('delta.feature.variantType-preview' = 'supported')
COMMENT 'Raw parsed documents from ai_parse_document with variant output'
AS (
  WITH files AS (
    SELECT
      path,
      content
    FROM STREAM READ_FILES(
      '/Volumes/main/default/source_documents/*.{pdf,jpg,jpeg,png}',
      format => 'binaryFile'
    )
  ),
  repartitioned_files AS (
    SELECT *
    FROM files
    DISTRIBUTE BY crc32(path) % 8  -- adjust partition count as needed
  )
  SELECT
    path,
    ai_parse_document(
      content,
      map(
        'version', '1.1',
        'imageOutputPath', '/Volumes/main/default/parsed_output/',
        'descriptionElementTypes', '*'
      )
    ) AS parsed,
    current_timestamp() AS parsed_at
  FROM repartitioned_files
)