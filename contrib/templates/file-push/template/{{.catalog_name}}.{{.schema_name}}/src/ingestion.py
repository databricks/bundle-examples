import dlt
from utils import tablemanager
from utils import formatmanager

def _make_append_flow(table_name, table_config, table_volume_path):
  def _body():
    # use _rescued_data as placeholder when no data file is present
    if not tablemanager.has_data_file(table_name):
      return tablemanager.get_placeholder_df_with_config(spark, table_config)
    else:
      return tablemanager.get_df_with_config(spark, table_config)

  # give the function a unique name
  _body.__name__ = f"append_{table_name.lower()}"

  # apply the decorator programmatically
  dlt.append_flow(target=table_name, name=table_name)(_body)

table_configs = tablemanager.get_configs()

# create the tables and append flows
for cfg in table_configs:
  tablemanager.validate_config(cfg)
  tbl = cfg["name"]
  path = tablemanager.get_table_volume_path(tbl)
  fmt = formatmanager.get_format_manager(cfg["format"])
  expts = fmt.expectations

  dlt.create_streaming_table(
    name=tbl,
    comment="File push created table",
    table_properties={"filepush.table_volume_path_data": path},
    expect_all=expts
  )
  _make_append_flow(tbl, cfg, path)
